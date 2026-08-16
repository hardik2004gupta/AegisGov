"""
Runtime Governance Middleware

Two distinct responsibilities:
1. Input Guardrails — detect prompt injection before anything executes.
2. Runtime Limit Enforcement — check budget counters during execution.

OPA answers: "Is this actor allowed to perform this action?"
This module answers: "Is this agent behaving safely within configured limits?"

Limits are read from centralized config (CLAUDE.md §7 — never hardcoded here):
    max_tool_calls          = 8
    max_execution_time      = 60 seconds
    max_agent_handoffs      = 4
    max_identical_tool_calls = 3
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from app.core.config import settings
from app.graph.state import AegisState

logger = logging.getLogger(__name__)


# ─── Prompt Injection Patterns ────────────────────────────────────────────────
# CLAUDE.md §7: lightweight first-line guardrail.
# This is NOT a complete prompt-injection defense — it is an MVP heuristic.

_INJECTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE), "ignore instructions"),
    (re.compile(r"reveal\s+(your\s+)?system\s+prompt", re.IGNORECASE), "reveal system prompt"),
    (re.compile(r"bypass\s+(governance|security|policy|rules)", re.IGNORECASE), "bypass governance"),
    (re.compile(r"disable\s+(security|governance|safety|restrictions)", re.IGNORECASE), "disable security"),
    (re.compile(r"dump\s+(credentials|secrets|passwords|tokens|keys)", re.IGNORECASE), "dump credentials"),
    (re.compile(r"reveal\s+(secrets?|credentials|passwords|tokens|api.?keys)", re.IGNORECASE), "reveal secrets"),
    (re.compile(r"(forget|ignore|disregard)\s+(your\s+)?(instructions|rules|guidelines|constraints)", re.IGNORECASE), "ignore rules"),
    (re.compile(r"you\s+are\s+now\s+(in\s+)?developer\s+mode", re.IGNORECASE), "developer mode"),
    (re.compile(r"act\s+as\s+(if\s+you\s+(are|have)\s+)?(no\s+restrictions|unrestricted|unlimited)", re.IGNORECASE), "no restrictions"),
    (re.compile(r"sudo\s+mode", re.IGNORECASE), "sudo mode"),
    (re.compile(r"jailbreak", re.IGNORECASE), "jailbreak"),
    (re.compile(r"DAN\s+mode", re.IGNORECASE), "DAN mode"),
]


def detect_injection(text: str) -> str | None:
    """Return the matched label if an injection pattern is detected, else None."""
    for pattern, label in _INJECTION_PATTERNS:
        if pattern.search(text):
            return label
    return None


async def check_input_guardrails(state: AegisState) -> dict[str, Any]:
    """LangGraph node: scan user input for prompt injection before any execution."""
    reason = detect_injection(state["message"])
    if reason:
        block_reason = f"Prompt injection detected: {reason}"
        logger.warning("Input blocked [%s] trace_id=%s", reason, state["trace_id"])

        try:
            from app.db.session import AsyncSessionLocal
            from app.governance.audit import Decision, EventType, audit_service
            async with AsyncSessionLocal() as db:
                await audit_service.record(
                    db,
                    trace_id=state["trace_id"],
                    user_id=state["user_id"],
                    agent_id="system",
                    action_type=EventType.INPUT_BLOCKED,
                    decision=Decision.BLOCKED,
                    reason=block_reason,
                    payload={},
                )
        except Exception as exc:
            logger.error("Failed to write INPUT_BLOCKED audit trace_id=%s: %s", state["trace_id"], exc)

        return {
            "governance_status": "BLOCKED",
            "block_reason": block_reason,
            "status": "BLOCKED",
            "output": "Your request was blocked by the security policy.",
        }
    return {"governance_status": "RUNNING"}


# ─── Runtime Limit Enforcement ────────────────────────────────────────────────


def check_runtime_limits(state: AegisState) -> dict[str, Any]:
    """Check whether the execution has exceeded any configured budget limit.

    Returns a non-empty dict (with BLOCKED status) if a limit is exceeded,
    or an empty dict if all limits are within bounds.
    """
    elapsed = time.monotonic() - state["execution_start_time"]
    if elapsed > settings.max_execution_time_seconds:
        return _budget_exceeded(
            state,
            f"execution time {elapsed:.1f}s exceeded {settings.max_execution_time_seconds}s limit",
        )

    if state["handoff_count"] >= settings.max_agent_handoffs:
        return _budget_exceeded(
            state,
            f"handoff count {state['handoff_count']} reached limit {settings.max_agent_handoffs}",
        )

    if state["tool_call_count"] >= settings.max_tool_calls:
        return _budget_exceeded(
            state,
            f"tool call count {state['tool_call_count']} reached limit {settings.max_tool_calls}",
        )

    # Detect identical tool call loops (CLAUDE.md §7)
    proposed = state.get("proposed_tool")
    if (
        proposed
        and state.get("last_tool_name") == proposed
        and state["identical_tool_call_count"] >= settings.max_identical_tool_calls
    ):
        return _budget_exceeded(
            state,
            f"identical tool '{proposed}' called {state['identical_tool_call_count']} times in a row "
            f"(limit: {settings.max_identical_tool_calls})",
        )

    return {}


def detect_handoff_loop(state: AegisState, candidate: str) -> str | None:
    """Detect repeated handoff cycles before accepting a new handoff.

    Returns a reason string if a loop is detected, else None.
    """
    history = list(state["handoff_history"])
    if not history:
        return None

    recent = history[-6:]

    # Same agent visited 3+ times in recent history
    if recent.count(candidate) >= 2:
        return (
            f"loop detected: '{candidate}' appeared {recent.count(candidate)} times "
            f"in recent handoff history {recent}"
        )

    # Alternating cycle: …A → B → A → B → candidate==A
    if len(recent) >= 3 and recent[-1] == recent[-3] == candidate:
        return f"alternating loop detected: {recent[-3]} → {recent[-2]} → {candidate}"

    return None


def _budget_exceeded(state: AegisState, reason: str) -> dict[str, Any]:
    logger.warning("Runtime budget exceeded trace_id=%s: %s", state["trace_id"], reason)
    return {
        "governance_status": "BLOCKED",
        "block_reason": reason,
        "status": "BLOCKED",
        "output": "Request stopped: runtime budget exceeded.",
    }
