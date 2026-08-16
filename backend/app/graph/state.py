# Phase 2: LangGraph State Schema
#
# Defines the shared state that flows through the LangGraph execution graph.
# State is immutable between nodes; each node returns a partial update.
#
# Canonical graph (CLAUDE.md §6):
#   START → identity_check → input_guardrails → supervisor_router →
#   handoff_authz → specialist_agent → tool_gateway_authz →
#   [execute_tool | approval_interrupt] → output_check → END

from __future__ import annotations

# TODO Phase 2: implement TypedDict/dataclass for LangGraph state
# Fields will include: user, agent_id, message, tool_proposals,
# governance_decisions, audit_events, runtime_counters, status
