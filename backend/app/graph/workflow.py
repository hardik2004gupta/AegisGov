"""
LangGraph Workflow — AegisGov Execution Graph

Phase 3 graph (CLAUDE.md §6):

    START
      ↓
    identity_check       ← JWT verified at API boundary; node logs context
      ↓
    input_guardrails     ← BLOCKED? → audit_block → END
      ↓
    supervisor_router    ← selects specialist agent
      ↓
    handoff_authz        ← OPA: DENIED? → audit_block → END
      ↓
    specialist_agent     ← dispatches to order/billing/admin agent
      ↓ [PROPOSAL_READY]
    tool_gateway         ← SecureToolGateway: 10-stage pipeline
      ├── ALLOWED         → END  (audit written inside gateway)
      ├── DENIED/BLOCKED  → audit_block → END
      └── PENDING_APPROVAL → approval_interrupt → END

Governance checks are first-class graph nodes (CLAUDE.md §6 — non-negotiable).
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.admin_agent import admin_agent_node
from app.agents.billing_agent import billing_agent_node
from app.agents.order_agent import order_agent_node
from app.agents.supervisor import supervisor_router_node
from app.core.security import ToolProposal
from app.db.session import AsyncSessionLocal
from app.governance.gateway import gateway
from app.governance.middleware import check_input_guardrails, check_runtime_limits
from app.governance.policy import policy_service
from app.graph.state import AegisState

logger = logging.getLogger(__name__)


# ─── Graph Nodes ──────────────────────────────────────────────────────────────


async def _identity_check_node(state: AegisState) -> dict[str, Any]:
    """Acknowledge that identity was verified at the API boundary.

    JWT was already validated by get_current_user; identity context
    (user_id, username, user_roles) is already present in state.
    Writes IDENTITY_VERIFIED audit event.
    """
    logger.info(
        "Identity check — user=%s roles=%s trace_id=%s",
        state["username"],
        state["user_roles"],
        state["trace_id"],
    )

    try:
        from app.governance.audit import Decision, EventType, audit_service
        async with AsyncSessionLocal() as db:
            await audit_service.record(
                db,
                trace_id=state["trace_id"],
                user_id=state["user_id"],
                agent_id="system",
                action_type=EventType.IDENTITY_VERIFIED,
                decision=Decision.ALLOWED,
                reason=f"JWT verified for user {state['username']} roles={state['user_roles']}",
                payload={"username": state["username"], "roles": state["user_roles"]},
            )
    except Exception as exc:
        logger.error("Failed to write IDENTITY_VERIFIED audit trace_id=%s: %s", state["trace_id"], exc)

    return {}


async def _handoff_authz_node(state: AegisState) -> dict[str, Any]:
    """Evaluate whether the user's roles authorize the selected agent handoff.

    Phase 3: delegates to OPA via policy_service.allow_handoff().
    Fail-closed: if OPA is unavailable, DENY.
    """
    target = state.get("selected_agent")
    if not target:
        return {
            "governance_status": "DENIED",
            "block_reason": "Supervisor did not select an agent",
            "status": "DENIED",
            "output": "Request denied: no agent could be selected for this request.",
        }

    result = await policy_service.allow_handoff(
        user_id=state["user_id"],
        user_roles=state["user_roles"],
        agent_id=state.get("agent_id") or "supervisor",
        agent_spiffe_id=state.get("agent_spiffe_id") or "aegis://agents/supervisor",
        target_agent=target,
    )

    if not result.allow:
        reason = (
            f"Roles {state['user_roles']} are not authorized to hand off to {target}"
        )
        logger.info(
            "Handoff DENIED user=%s roles=%s target=%s trace_id=%s reason=%s",
            state["username"],
            state["user_roles"],
            target,
            state["trace_id"],
            result.reason,
        )
        try:
            from app.governance.audit import Decision, EventType, audit_service
            async with AsyncSessionLocal() as db:
                await audit_service.record(
                    db,
                    trace_id=state["trace_id"],
                    user_id=state["user_id"],
                    agent_id=state.get("agent_id") or "supervisor",
                    action_type=EventType.AGENT_HANDOFF_DENIED,
                    decision=Decision.DENIED,
                    reason=reason,
                    payload={"target_agent": target, "roles": state["user_roles"]},
                )
        except Exception as exc:
            logger.error("Failed to write HANDOFF_DENIED audit trace_id=%s: %s", state["trace_id"], exc)
        return {
            "governance_status": "DENIED",
            "block_reason": reason,
            "status": "DENIED",
            "output": "Access denied: your role does not permit this operation.",
        }

    logger.info(
        "Handoff ALLOWED user=%s target=%s trace_id=%s",
        state["username"],
        target,
        state["trace_id"],
    )
    try:
        from app.governance.audit import Decision, EventType, audit_service
        async with AsyncSessionLocal() as db:
            await audit_service.record(
                db,
                trace_id=state["trace_id"],
                user_id=state["user_id"],
                agent_id=state.get("agent_id") or "supervisor",
                action_type=EventType.AGENT_HANDOFF_ALLOWED,
                decision=Decision.ALLOWED,
                reason=f"Handoff to {target} authorized for roles {state['user_roles']}",
                payload={"target_agent": target, "roles": state["user_roles"]},
            )
    except Exception as exc:
        logger.error("Failed to write HANDOFF_ALLOWED audit trace_id=%s: %s", state["trace_id"], exc)
    return {"governance_status": "RUNNING"}


def _specialist_agent_dispatch(state: AegisState) -> dict[str, Any]:
    """Dispatch to the appropriate specialist agent based on selected_agent.

    The specialist produces a ToolProposal stored in state.
    It MUST NOT call any database function or tool handler.
    """
    # Check runtime limits before dispatching specialist
    limit_result = check_runtime_limits(state)
    if limit_result:
        return limit_result

    agent = state.get("selected_agent")
    if agent == "order-agent":
        return order_agent_node(state)
    if agent == "billing-agent":
        return billing_agent_node(state)
    if agent == "admin-agent":
        return admin_agent_node(state)

    return {
        "status": "FAILED",
        "error": f"Unknown agent: {agent!r}",
        "governance_status": "DENIED",
    }


async def _tool_gateway_node(state: AegisState) -> dict[str, Any]:
    """Execute the proposed tool through the Secure Tool Gateway.

    Builds a ToolProposal from state, opens a DB session, and invokes
    the full 10-stage gateway pipeline. Maps GatewayResult back to state.

    INVARIANT 1: Agents never reach this node directly.
    """
    proposed_tool = state.get("proposed_tool")
    if not proposed_tool:
        return {
            "governance_status": "DENIED",
            "status": "DENIED",
            "block_reason": "Specialist produced no tool proposal",
            "output": "Agent did not produce a tool proposal.",
        }

    proposal = ToolProposal(
        tool_name=proposed_tool,
        arguments=state.get("tool_arguments") or {},
        agent_id=state.get("agent_id") or "",
        agent_spiffe_id=state.get("agent_spiffe_id") or "",
        thread_id=state["thread_id"],
        reason=state.get("proposal_reason") or "",
    )

    async with AsyncSessionLocal() as db:
        result = await gateway.execute(proposal, state, db)

    if result.decision == "ALLOWED":
        new_tool_count = state["tool_call_count"] + 1
        last = state.get("last_tool_name")
        identical = (
            (state["identical_tool_call_count"] + 1) if last == proposed_tool else 1
        )
        return {
            "governance_status": "ALLOWED",
            "status": "COMPLETED",
            "risk_level": result.risk_level,
            "execution_result": result.result,
            "execution_time_ms": result.execution_time_ms,
            "output": _format_tool_result(proposed_tool, result.result),
            "tool_call_count": new_tool_count,
            "last_tool_name": proposed_tool,
            "identical_tool_call_count": identical,
        }

    if result.decision == "PENDING_APPROVAL":
        return {
            "governance_status": "PENDING_APPROVAL",
            "status": "INTERRUPTED_PENDING_APPROVAL",
            "risk_level": result.risk_level,
            "requires_approval": True,
            "approval_id": result.approval_id,
            "output": (
                f"Operation paused for human approval (approval_id={result.approval_id}). "
                "An authorized admin must review and approve this action."
            ),
        }

    # DENIED or BLOCKED
    return {
        "governance_status": result.decision,
        "status": result.decision,
        "block_reason": result.reason,
        "output": f"Request {result.decision.lower()}: {result.reason}",
    }


def _approval_interrupt_node(state: AegisState) -> dict[str, Any]:
    """Terminal node for executions paused awaiting human approval."""
    logger.info(
        "Execution paused for HITL approval_id=%s trace_id=%s",
        state.get("approval_id"),
        state["trace_id"],
    )
    return {}


def _audit_block_node(state: AegisState) -> dict[str, Any]:
    """Terminal node for BLOCKED or DENIED executions."""
    logger.info(
        "Execution ended [%s] reason=%s trace_id=%s",
        state["governance_status"],
        state.get("block_reason"),
        state["trace_id"],
    )
    return {}


# ─── Conditional edge routing ─────────────────────────────────────────────────


def _route_after_guardrails(state: AegisState) -> str:
    if state["governance_status"] == "BLOCKED":
        return "audit_block"
    return "supervisor_router"


def _route_after_handoff_authz(state: AegisState) -> str:
    if state["governance_status"] in ("BLOCKED", "DENIED"):
        return "audit_block"
    return "specialist_agent"


def _route_after_specialist(state: AegisState) -> str:
    gs = state.get("governance_status", "RUNNING")
    s = state.get("status", "RUNNING")
    if gs in ("BLOCKED", "DENIED", "FAILED") or s in ("BLOCKED", "DENIED", "FAILED"):
        return "audit_block"
    return "tool_gateway"


def _route_after_tool_gateway(state: AegisState) -> str:
    gs = state.get("governance_status", "DENIED")
    if gs == "ALLOWED":
        return END
    if gs == "PENDING_APPROVAL":
        return "approval_interrupt"
    return "audit_block"


# ─── Output formatting ────────────────────────────────────────────────────────


def _format_tool_result(tool_name: str, result: dict | None) -> str:
    """Produce a human-readable summary of a tool execution result."""
    if not result:
        return f"Tool {tool_name!r} executed successfully."
    if tool_name == "get_order":
        return (
            f"Order #{result.get('order_id')}: status={result.get('status')}, "
            f"amount=${result.get('total_amount', 0):.2f} {result.get('currency', 'USD')}."
        )
    if tool_name == "get_customer":
        return (
            f"Customer #{result.get('customer_id')}: {result.get('full_name')}, "
            f"email={result.get('email')}."
        )
    if tool_name == "get_payment":
        return (
            f"Payment #{result.get('payment_id')} for order #{result.get('order_id')}: "
            f"amount=${result.get('amount', 0):.2f}, status={result.get('status')}."
        )
    if tool_name == "issue_refund":
        return (
            f"Refund of ${result.get('refund_amount', 0):.2f} issued for "
            f"order #{result.get('order_id')}. Status: {result.get('status')}."
        )
    if tool_name == "delete_customer":
        return (
            f"Customer #{result.get('customer_id')} ({result.get('full_name')}) "
            f"has been permanently deleted."
        )
    return f"Tool {tool_name!r} completed: {result}"


# ─── Graph compilation ────────────────────────────────────────────────────────


def _build_graph() -> StateGraph:
    g = StateGraph(AegisState)

    # Register nodes
    g.add_node("identity_check", _identity_check_node)
    g.add_node("input_guardrails", check_input_guardrails)
    g.add_node("supervisor_router", supervisor_router_node)
    g.add_node("handoff_authz", _handoff_authz_node)
    g.add_node("specialist_agent", _specialist_agent_dispatch)
    g.add_node("tool_gateway", _tool_gateway_node)
    g.add_node("approval_interrupt", _approval_interrupt_node)
    g.add_node("audit_block", _audit_block_node)

    # Wire edges
    g.add_edge(START, "identity_check")
    g.add_edge("identity_check", "input_guardrails")
    g.add_conditional_edges(
        "input_guardrails",
        _route_after_guardrails,
        {"audit_block": "audit_block", "supervisor_router": "supervisor_router"},
    )
    g.add_edge("supervisor_router", "handoff_authz")
    g.add_conditional_edges(
        "handoff_authz",
        _route_after_handoff_authz,
        {"audit_block": "audit_block", "specialist_agent": "specialist_agent"},
    )
    g.add_conditional_edges(
        "specialist_agent",
        _route_after_specialist,
        {"audit_block": "audit_block", "tool_gateway": "tool_gateway"},
    )
    g.add_conditional_edges(
        "tool_gateway",
        _route_after_tool_gateway,
        {END: END, "approval_interrupt": "approval_interrupt", "audit_block": "audit_block"},
    )
    g.add_edge("approval_interrupt", END)
    g.add_edge("audit_block", END)

    return g


# Compile once at module load. The compiled graph is the sole execution path.
compiled_graph = _build_graph().compile()
