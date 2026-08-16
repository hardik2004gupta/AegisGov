"""
Supervisor Agent

Responsibilities (CLAUDE.md §4):
    - Understand user intent from the message
    - Select the appropriate specialist agent
    - Request an authorized handoff (evaluated in handoff_authz node)
    - NEVER directly execute privileged tools

Workload identity: aegis://agents/supervisor

Routing strategy:
    1. If OPENAI_API_KEY is configured: use LLM for natural-language routing.
    2. Otherwise: deterministic keyword/pattern matching (reliable for demos).
       The deterministic path is NOT a fallback hack — it demonstrates the
       governance architecture independently of any LLM API availability.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.core.config import settings
from app.core.security import SUPERVISOR_IDENTITY
from app.graph.state import AegisState

logger = logging.getLogger(__name__)


# ─── Deterministic Intent Router ─────────────────────────────────────────────
# Ordered most-specific → least-specific.
# Admin patterns checked first to prevent billing keywords from catching
# "delete billing account" as billing-agent.

_ADMIN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"delete\b.*?\b(customer|account|user)\b", re.IGNORECASE),
    re.compile(r"remove\b.*?\b(customer|account|user)\b", re.IGNORECASE),
    re.compile(r"purge\s+customer", re.IGNORECASE),
    re.compile(r"erase\s+customer", re.IGNORECASE),
]

_BILLING_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"refund", re.IGNORECASE),
    re.compile(r"payment", re.IGNORECASE),
    re.compile(r"billing", re.IGNORECASE),
    re.compile(r"invoice", re.IGNORECASE),
    re.compile(r"charge", re.IGNORECASE),
    re.compile(r"\$\s*\d+", re.IGNORECASE),         # dollar amount
    re.compile(r"issue\s+a?\s*refund", re.IGNORECASE),
    re.compile(r"paid", re.IGNORECASE),
]


def _deterministic_route(message: str) -> str:
    """Route intent to an agent name based on keyword patterns."""
    for p in _ADMIN_PATTERNS:
        if p.search(message):
            return "admin-agent"
    for p in _BILLING_PATTERNS:
        if p.search(message):
            return "billing-agent"
    return "order-agent"


async def _llm_route(message: str) -> str | None:
    """LLM-based routing when an OpenAI key is configured.

    Returns the agent name or None if the LLM is unavailable or fails.
    Falls back gracefully so the deterministic router takes over.
    """
    if not settings.openai_api_key:
        return None
    try:
        from langchain_openai import ChatOpenAI  # noqa: PLC0415
        from langchain_core.messages import HumanMessage, SystemMessage  # noqa: PLC0415

        llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0.0,
            api_key=settings.openai_api_key,  # type: ignore[arg-type]
        )
        system = (
            "You are an intent router. Reply with EXACTLY one of: "
            "'order-agent', 'billing-agent', or 'admin-agent'. "
            "Use order-agent for: viewing orders, customer info. "
            "Use billing-agent for: payments, refunds, billing. "
            "Use admin-agent for: deleting customers. "
            "Output ONLY the agent name — no punctuation, no explanation."
        )
        result = await llm.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=message)]
        )
        choice = str(result.content).strip().lower()
        if choice in ("order-agent", "billing-agent", "admin-agent"):
            return choice
        logger.warning("LLM returned unexpected agent choice: %r", choice)
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM routing failed, using deterministic fallback: %s", exc)
    return None


async def supervisor_router_node(state: AegisState) -> dict[str, Any]:
    """LangGraph node: Supervisor selects a specialist agent.

    Uses LLM when configured; deterministic pattern matching otherwise.
    The supervisor sets selected_agent; handoff_authz validates the choice.
    The supervisor NEVER executes tools directly (INVARIANT 1, CLAUDE.md §26).
    """
    selected = await _llm_route(state["message"])
    if selected is None:
        selected = _deterministic_route(state["message"])

    logger.info(
        "Supervisor selected agent=%s trace_id=%s",
        selected,
        state["trace_id"],
    )

    return {
        "selected_agent": selected,
        # Record supervisor as the current agent during routing phase
        "agent_id": SUPERVISOR_IDENTITY.agent_id,
        "agent_spiffe_id": SUPERVISOR_IDENTITY.spiffe_id,
    }
