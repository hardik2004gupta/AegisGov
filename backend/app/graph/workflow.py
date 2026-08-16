"""
LangGraph Workflow — AegisGov Execution Graph

Canonical Phase 2 graph (CLAUDE.md §6):

    START
      ↓
    identity_check       ← identity verified at API boundary; node acknowledges context
      ↓
    input_guardrails     ← BLOCKED? → audit_block → END
      ↓
    supervisor_router    ← selects specialist agent
      ↓
    handoff_authz        ← DENIED? → audit_block → END
      ↓
    specialist_agent     ← dispatches to order/billing/admin agent
      ↓
    END

    (Phase 3 extends: specialist_agent → tool_gateway_authz → execute/hitl → END)

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
from app.governance.middleware import check_input_guardrails, check_runtime_limits
from app.governance.policy import policy_service
from app.graph.state import AegisState

logger = logging.getLogger(__name__)


# ─── Graph Nodes ──────────────────────────────────────────────────────────────


def _identity_check_node(state: AegisState) -> dict[str, Any]:
    """Acknowledge that identity was verified at the API boundary.

    In Phase 2 the JWT was already validated by get_current_user; the identity
    context (user_id, username, user_roles) is already present in state.
    This node exists as a named checkpoint in the graph so Phase 3+ can add
    additional identity assertions here without changing the graph topology.
    """
    logger.info(
        "Identity check — user=%s roles=%s trace_id=%s",
        state["username"],
        state["user_roles"],
        state["trace_id"],
    )
    return {}


def _handoff_authz_node(state: AegisState) -> dict[str, Any]:
    """Evaluate whether the user's roles authorize the selected agent handoff.

    Phase 2: uses PolicyDecisionService with deterministic role-agent mapping.
    Phase 3: PolicyDecisionService will delegate to OPA (same interface).
    """
    target = state.get("selected_agent")
    if not target:
        return {
            "governance_status": "DENIED",
            "block_reason": "Supervisor did not select an agent",
            "status": "DENIED",
            "output": "Request denied: no agent could be selected for this request.",
        }

    allowed = policy_service.allow_handoff(state["user_roles"], target)

    if not allowed:
        reason = (
            f"Roles {state['user_roles']} are not authorized to hand off to {target}"
        )
        logger.info(
            "Handoff DENIED user=%s roles=%s target=%s trace_id=%s",
            state["username"],
            state["user_roles"],
            target,
            state["trace_id"],
        )
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
    return {"governance_status": "RUNNING"}


def _specialist_agent_dispatch(state: AegisState) -> dict[str, Any]:
    """Dispatch to the appropriate specialist agent based on selected_agent.

    The specialist receives the state and returns a ToolProposal embedded in
    state updates. It MUST NOT call any database function or tool handler.
    """
    # Check runtime limits before handing off to specialist
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


def _audit_block_node(state: AegisState) -> dict[str, Any]:
    """Terminal node for BLOCKED or DENIED executions.

    Phase 4 will add persistent audit event writes here.
    """
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


# ─── Graph compilation ────────────────────────────────────────────────────────


def _build_graph() -> StateGraph:
    g = StateGraph(AegisState)

    # Register nodes
    g.add_node("identity_check", _identity_check_node)
    g.add_node("input_guardrails", check_input_guardrails)
    g.add_node("supervisor_router", supervisor_router_node)
    g.add_node("handoff_authz", _handoff_authz_node)
    g.add_node("specialist_agent", _specialist_agent_dispatch)
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
    g.add_edge("specialist_agent", END)
    g.add_edge("audit_block", END)

    return g


# Compile once at module load. The compiled graph is the sole execution path.
compiled_graph = _build_graph().compile()
