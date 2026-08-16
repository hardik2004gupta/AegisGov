"""
Order Agent — Specialist for order and customer read operations.

Workload identity: aegis://agents/order-agent
Capabilities:      get_order, get_customer

INVARIANT 1 (CLAUDE.md §26): This agent produces a ToolProposal only.
It does NOT call any database function, handler, or SQLAlchemy session.
Phase 3's Secure Tool Gateway will route the proposal through:
    Registry → Pydantic Validation → OPA → Risk → [HITL?] → Execute
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.core.security import ORDER_AGENT_IDENTITY
from app.graph.state import AegisState

logger = logging.getLogger(__name__)

# ─── Parameter extractors ─────────────────────────────────────────────────────

_ORDER_RE = re.compile(r"order\s*#?\s*(\d+)", re.IGNORECASE)
_CUSTOMER_RE = re.compile(r"customer\s*#?\s*(\d+)", re.IGNORECASE)


def _extract_order_id(message: str) -> int | None:
    m = _ORDER_RE.search(message)
    return int(m.group(1)) if m else None


def _extract_customer_id(message: str) -> int | None:
    m = _CUSTOMER_RE.search(message)
    return int(m.group(1)) if m else None


# ─── Agent node ───────────────────────────────────────────────────────────────


def order_agent_node(state: AegisState) -> dict[str, Any]:
    """LangGraph node: produce a get_order or get_customer proposal.

    Selection logic: prefer get_customer when customer_id is mentioned without
    an order_id; default to get_order otherwise.
    """
    agent = ORDER_AGENT_IDENTITY
    message = state["message"]

    customer_id = _extract_customer_id(message)
    order_id = _extract_order_id(message)

    if customer_id is not None and order_id is None:
        tool = "get_customer"
        arguments: dict[str, Any] = {"customer_id": customer_id}
        reason = f"User requested customer info for customer #{customer_id}"
    else:
        oid = order_id if order_id is not None else 1
        tool = "get_order"
        arguments = {"order_id": oid}
        reason = f"User requested order info for order #{oid}"

    logger.info(
        "order-agent proposal tool=%s args=%s trace_id=%s",
        tool,
        arguments,
        state["trace_id"],
    )

    return {
        "agent_id": agent.agent_id,
        "agent_spiffe_id": agent.spiffe_id,
        "agent_capabilities": agent.capabilities,
        "handoff_count": state["handoff_count"] + 1,
        "handoff_history": state["handoff_history"] + [agent.agent_id],
        "proposed_tool": tool,
        "tool_arguments": arguments,
        "proposal_reason": reason,
        "governance_status": "PROPOSAL_READY",
        "status": "PROPOSAL_READY",
        "output": f"Proposed action: {tool}({arguments}). Awaiting Secure Tool Gateway.",
    }
