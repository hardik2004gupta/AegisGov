# Phase 3: OPA Policy Client
#
# This module is the sole interface to the OPA policy server.
# Authorization logic must NOT be duplicated elsewhere (CLAUDE.md §11).
#
# Fail-closed contract (CLAUDE.md §11):
#   OPA unavailable          → DENY
#   Unknown tool             → DENY
#   Missing identity         → DENY
#   Invalid OPA response     → DENY
#   Policy error             → DENY
#
# Input to OPA (CLAUDE.md §11):
# {
#   "input": {
#     "user":    { "id": "...", "roles": ["billing"] },
#     "agent":   { "id": "...", "spiffe_id": "aegis://agents/billing-agent" },
#     "action":  { "type": "tool_execution", "name": "issue_refund" },
#     "resource": { "type": "order", "id": "8829" }
#   }
# }
#
# Expected OPA output:
# { "allow": bool, "require_human_approval": bool }

from __future__ import annotations

# TODO Phase 3: implement httpx-based OPA REST client with fail-closed behavior
