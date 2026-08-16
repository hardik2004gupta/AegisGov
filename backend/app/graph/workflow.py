# Phase 2: LangGraph Workflow Definition
#
# Wires together all graph nodes into the canonical execution graph.
# Governance checks are first-class nodes — not an external side process.
#
# Graph nodes (CLAUDE.md §6):
#   identity_check     — verify Keycloak JWT
#   input_guardrails   — prompt injection detection
#   supervisor_router  — select specialist agent
#   handoff_authz      — OPA: can this user reach this agent?
#   specialist_agent   — propose tool call
#   tool_gateway_authz — full gateway pipeline (registry→pydantic→OPA→risk)
#   execute_tool       — secure execution via least-privilege DB role
#   approval_interrupt — pause graph for human review
#   output_check       — sanitize and validate response
#   audit_block        — record DENY/BLOCK decisions

from __future__ import annotations

# TODO Phase 2: construct and compile the LangGraph StateGraph
