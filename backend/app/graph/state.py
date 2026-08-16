"""
LangGraph State Schema

Defines the shared state that flows through every node in the execution graph.
Each node returns a dict of partial updates; LangGraph merges them into state.

Canonical graph (CLAUDE.md §6):
    START → identity_check → input_guardrails → supervisor_router →
    handoff_authz → specialist_agent → END
    (Phase 3 extends: specialist_agent → tool_gateway_authz → ...)
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Optional
from typing import TypedDict


def _new_trace_id() -> str:
    return f"trc_{uuid.uuid4().hex[:8]}"


class AegisState(TypedDict):
    # ─── Identity ─────────────────────────────────────────────────────────────
    thread_id: str
    user_id: str
    username: str
    user_roles: list[str]

    # ─── Active agent ─────────────────────────────────────────────────────────
    agent_id: Optional[str]
    agent_spiffe_id: Optional[str]
    agent_capabilities: list[str]

    # ─── Input ────────────────────────────────────────────────────────────────
    message: str

    # ─── Routing ──────────────────────────────────────────────────────────────
    selected_agent: Optional[str]
    handoff_history: list[str]

    # ─── Runtime counters (CLAUDE.md §7 — never hardcode the limits here) ────
    tool_call_count: int
    handoff_count: int
    execution_start_time: float
    last_tool_name: Optional[str]
    identical_tool_call_count: int

    # ─── Tool Proposal (Phase 2 output — Phase 3 routes through gateway) ──────
    proposed_tool: Optional[str]
    tool_arguments: Optional[dict[str, Any]]
    proposal_reason: Optional[str]

    # ─── Governance ───────────────────────────────────────────────────────────
    # Values: RUNNING | ALLOWED | DENIED | BLOCKED | PROPOSAL_READY
    governance_status: str
    block_reason: Optional[str]

    # ─── Observability ────────────────────────────────────────────────────────
    trace_id: str

    # ─── Output ───────────────────────────────────────────────────────────────
    # status values: RUNNING | PROPOSAL_READY | DENIED | BLOCKED | FAILED
    output: Optional[str]
    error: Optional[str]
    status: str


def initial_state(
    *,
    thread_id: str,
    user_id: str,
    username: str,
    user_roles: list[str],
    message: str,
    trace_id: str | None = None,
) -> AegisState:
    """Build a fully-initialized state for a new graph execution."""
    return AegisState(
        thread_id=thread_id,
        user_id=user_id,
        username=username,
        user_roles=user_roles,
        agent_id=None,
        agent_spiffe_id=None,
        agent_capabilities=[],
        message=message,
        selected_agent=None,
        handoff_history=[],
        tool_call_count=0,
        handoff_count=0,
        execution_start_time=time.monotonic(),
        last_tool_name=None,
        identical_tool_call_count=0,
        proposed_tool=None,
        tool_arguments=None,
        proposal_reason=None,
        governance_status="RUNNING",
        block_reason=None,
        trace_id=trace_id or _new_trace_id(),
        output=None,
        error=None,
        status="RUNNING",
    )
