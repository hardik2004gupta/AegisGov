# Phase 3: Runtime Governance Middleware
#
# Enforces the behavioral limits defined in CLAUDE.md §7.
# This is a separate concern from OPA policy authorization.
#
# OPA answers: "Is this actor allowed to perform this action?"
# Runtime governance answers: "Is this agent behaving safely?"
#
# Limits (centralized in config.py — never hardcoded inline):
#   max_tool_calls         = 8
#   max_execution_time     = 60 seconds
#   max_agent_handoffs     = 4
#   max_identical_tool_calls = 3
#
# Detects:
#   - Tool budget exhaustion
#   - Agent handoff loops (Order→Billing→Order→Billing→...)
#   - Excessive identical tool calls (get_order×3)
#   - Execution time exceeded
#   - Prompt injection patterns in input_guardrails node

from __future__ import annotations

# TODO Phase 3: implement runtime limit enforcement and loop detection
