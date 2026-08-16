"""
Risk Classification Engine — CLAUDE.md §14, §18-20

Classifies tool proposals by risk level and determines whether human
approval is required before execution. This module is deterministic —
all thresholds and mappings are centralized here, never scattered
through handlers or middleware.

Risk levels (CLAUDE.md §14):
    LOW      — get_order, get_customer       → auto-execute
    MEDIUM   — get_payment                  → auto-execute
    HIGH     — issue_refund                 → auto if ≤$500; HITL if >$500
    CRITICAL — delete_customer              → HITL always

CLAUDE.md §19: "The $500 threshold must be centralized configuration/policy logic."
"""

from __future__ import annotations

from typing import Literal

RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# Centralized $500 HITL threshold (CLAUDE.md §19 — must not be scattered)
REFUND_HITL_THRESHOLD: float = 500.0

# Tool → base risk level mapping
_TOOL_RISK_MAP: dict[str, RiskLevel] = {
    "get_order": "LOW",
    "get_customer": "LOW",
    "get_payment": "MEDIUM",
    "issue_refund": "HIGH",
    "delete_customer": "CRITICAL",
}


def classify_risk(tool_name: str, arguments: dict) -> RiskLevel:
    """Return the risk level for a tool execution.

    Unknown tools are classified as CRITICAL (fail-closed behavior).
    """
    return _TOOL_RISK_MAP.get(tool_name, "CRITICAL")


def requires_hitl(tool_name: str, arguments: dict, risk_level: RiskLevel) -> bool:
    """Determine whether this operation requires human approval.

    CRITICAL always requires HITL.
    HIGH requires HITL only when the refund amount exceeds the threshold.

    This is the definitive runtime HITL decision point.
    OPA also signals require_human_approval; both are checked as defense-in-depth.
    """
    if risk_level == "CRITICAL":
        return True
    if tool_name == "issue_refund":
        amount = float(arguments.get("amount", 0))
        return amount > REFUND_HITL_THRESHOLD
    return False
