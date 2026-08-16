# Phase 2: Supervisor Agent
#
# The Supervisor is the LangGraph entry-point agent.
# Responsibilities (CLAUDE.md §4):
#   - Understand user intent from the message
#   - Select the appropriate specialist agent
#   - Request an authorized handoff via OPA
#   - NEVER directly execute privileged tools
#
# Workload identity: aegis://agents/supervisor

from __future__ import annotations

# TODO Phase 2: implement supervisor node for LangGraph workflow
