"""
Billing Agent — Specialist for payment and refund operations.

Workload identity: aegis://agents/billing-agent
Capabilities:      get_order, get_payment, issue_refund

INVARIANT 1 (CLAUDE.md §26): This agent produces a ToolProposal only.
No refund is issued here. No database access. No handler is invoked.

Phase 3 note: issue_refund > $500 will trigger HITL (CLAUDE.md §14).
That logic lives in the Risk module and HITL gateway — not in this agent.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.core.security import BILLING_AGENT_IDENTITY
from app.graph.state import AegisState

logger = logging.getLogger(__name__)

# ─── Parameter extractors ─────────────────────────────────────────────────────

_ORDER_RE = re.compile(r"order\s*#?\s*(\d+)", re.IGNORECASE)
_AMOUNT_RE = re.compile(r"\$\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
_REFUND_RE = re.compile(r"refund", re.IGNORECASE)
_PAYMENT_RE = re.compile(r"payment|paid|invoice", re.IGNORECASE)


def _extract_order_id(message: str) -> int | None:
    m = _ORDER_RE.search(message)
    return int(m.group(1)) if m else None


def _extract_amount(message: str) -> float | None:
    m = _AMOUNT_RE.search(message)
    return float(m.group(1)) if m else None


def _extract_reason(message: str) -> str:
    """Build a short reason string from the message."""
    # Use the original message, capped for the reason field
    clean = message.strip()
    return clean[:200] if len(clean) > 200 else clean


# ─── Agent node ───────────────────────────────────────────────────────────────


def billing_agent_node(state: AegisState) -> dict[str, Any]:
    """LangGraph node: produce a get_payment or issue_refund proposal.

    Selection logic:
        - 'refund' keyword → issue_refund
        - Otherwise → get_payment (show payment info for an order)
    """
    agent = BILLING_AGENT_IDENTITY
    message = state["message"]

    order_id = _extract_order_id(message)
    amount = _extract_amount(message)

    if _REFUND_RE.search(message):
        tool = "issue_refund"
        oid = order_id if order_id is not None else 1
        arguments: dict[str, Any] = {
            "order_id": oid,
            "amount": amount if amount is not None else 0.0,
            "reason": _extract_reason(message),
        }
        reason = f"User requested a refund of ${arguments['amount']} for order #{oid}"
    else:
        oid = order_id if order_id is not None else 1
        tool = "get_payment"
        arguments = {"order_id": oid}
        reason = f"User requested payment info for order #{oid}"

    logger.info(
        "billing-agent proposal tool=%s args=%s trace_id=%s",
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
