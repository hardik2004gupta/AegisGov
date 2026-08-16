"""
Admin Agent — Specialist for administrative operations.

Workload identity: aegis://agents/admin-agent
Capabilities:      get_customer, delete_customer

Authorized by: admin role ONLY (CLAUDE.md §13).

INVARIANT 1 (CLAUDE.md §26): This agent produces a ToolProposal only.
No deletion occurs here. No database access. No handler is invoked.

INVARIANT 5 (CLAUDE.md §26): delete_customer is CRITICAL risk.
Phase 3's Secure Tool Gateway will ALWAYS pause for human approval
before executing any deletion. This agent just proposes.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.core.security import ADMIN_AGENT_IDENTITY
from app.graph.state import AegisState

logger = logging.getLogger(__name__)

# ─── Parameter extractors ─────────────────────────────────────────────────────

_CUSTOMER_RE = re.compile(r"customer\s*#?\s*(\d+)", re.IGNORECASE)
_DELETE_RE = re.compile(r"delete|remove|purge|erase", re.IGNORECASE)


def _extract_customer_id(message: str) -> int | None:
    m = _CUSTOMER_RE.search(message)
    return int(m.group(1)) if m else None


# ─── Agent node ───────────────────────────────────────────────────────────────


def admin_agent_node(state: AegisState) -> dict[str, Any]:
    """LangGraph node: produce a get_customer or delete_customer proposal.

    Selection logic:
        - delete/remove/purge keyword → delete_customer
        - Otherwise → get_customer
    """
    agent = ADMIN_AGENT_IDENTITY
    message = state["message"]
    customer_id = _extract_customer_id(message)

    if _DELETE_RE.search(message):
        tool = "delete_customer"
        cid = customer_id if customer_id is not None else 1
        arguments: dict[str, Any] = {"customer_id": cid}
        reason = f"User requested deletion of customer #{cid}"
    else:
        cid = customer_id if customer_id is not None else 1
        tool = "get_customer"
        arguments = {"customer_id": cid}
        reason = f"User requested info for customer #{cid}"

    logger.info(
        "admin-agent proposal tool=%s args=%s trace_id=%s",
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
