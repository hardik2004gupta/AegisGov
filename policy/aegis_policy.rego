package aegis

import rego.v1

# ============================================================
# AegisGov Policy — Phase 1 Infrastructure Placeholder
#
# Phase 3 implements the full authorization rules.
# This file establishes the package structure, documents the
# expected input/output contract, and ensures OPA starts
# successfully with a valid policy.
#
# PERMANENT CONTRACT:
#   - Default deny (fail closed) is enforced here and must
#     never be changed to default allow.
#   - Phase 3 will add allow rules on top of these defaults.
#   - OPA is the sole policy decision point (CLAUDE.md §11).
#
# Expected input shape:
# {
#   "user":    { "id": "...", "roles": ["analyst"] },
#   "agent":   { "id": "...", "spiffe_id": "aegis://agents/..." },
#   "action":  { "type": "tool_execution | agent_handoff", "name": "..." },
#   "resource": { "type": "...", "id": "..." }
# }
#
# Expected output shape:
# {
#   "allow":                  bool,
#   "require_human_approval": bool
# }
# ============================================================

# Default deny — fail closed is the permanent security contract.
# Phase 3 adds specific allow rules.
default allow := false

# Default: no human approval required for denied actions
# (human approval applies only after allow is granted).
default require_human_approval := false

# ─── Phase 3 stubs ──────────────────────────────────────────
# The following rule skeletons document the full authorization
# logic to be implemented in Phase 3.

# agent_handoff_allowed will enforce role → agent policy:
#   analyst → order-agent
#   billing → order-agent, billing-agent
#   admin   → order-agent, billing-agent, admin-agent

# tool_execution_allowed will enforce:
#   UserPermission AND AgentCapability AND ValidTool
#   AND ValidParameters AND RuntimeSafe

# high_value_refund will trigger HITL for refund > 500
# critical_tool will always require HITL (e.g. delete_customer)
