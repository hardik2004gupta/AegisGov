package aegis

import rego.v1

# =============================================================================
# AegisGov Authorization Policy
# CLAUDE.md §11-15
#
# Input schema:
#   input.user     { id: str, roles: [str] }
#   input.agent    { id: str, spiffe_id: str }
#   input.action   { type: "agent_handoff"|"tool_execution", name: str, amount?: float }
#   input.resource { type: str, id: str }
#
# Output:
#   allow                  bool    — is the action authorized?
#   require_human_approval bool    — must a human approve before execution?
#   reason                 string  — human-readable decision rationale
#
# FAIL-CLOSED: default deny. OPA is the sole policy decision point (CLAUDE.md §24 Rule 4).
# =============================================================================

# ─── Default deny (permanent — CLAUDE.md §24 Rule 1) ─────────────────────────
default allow := false
default require_human_approval := false
default reason := "denied by default policy"

# ─── Agent Handoff Authorization (CLAUDE.md §13) ─────────────────────────────
# Supervisor may hand off to a specialist only when the user's role permits it.

allow if {
	input.action.type == "agent_handoff"
	some role in input.user.roles
	input.action.name in _role_agent_policy[role]
}

# ─── Tool Execution Authorization (CLAUDE.md §12) ────────────────────────────
# All conditions required simultaneously (CLAUDE.md §12 authorization equation):
#   1. User's role permits the tool
#   2. Agent's capability includes the tool

allow if {
	input.action.type == "tool_execution"
	some role in input.user.roles
	input.action.name in _role_tool_policy[role]
	input.action.name in _agent_tool_capability[input.agent.id]
}

# ─── Human Approval Requirements (CLAUDE.md §14-15) ──────────────────────────
# Only applies when the action is already allowed.

# delete_customer always requires human approval (CRITICAL risk)
require_human_approval if {
	allow
	input.action.type == "tool_execution"
	input.action.name == "delete_customer"
}

# issue_refund > $500 requires human approval (HIGH risk threshold)
require_human_approval if {
	allow
	input.action.type == "tool_execution"
	input.action.name == "issue_refund"
	amount := object.get(input.action, "amount", 0)
	amount > 500
}

# ─── Decision Reasons ─────────────────────────────────────────────────────────
reason := "allowed" if {
	allow
	not require_human_approval
}

reason := "allowed: requires human approval" if {
	allow
	require_human_approval
}

# ─── Role → Agent Policy (CLAUDE.md §13) ─────────────────────────────────────
_role_agent_policy := {
	"analyst": {"order-agent"},
	"billing": {"order-agent", "billing-agent"},
	"admin": {"order-agent", "billing-agent", "admin-agent"},
}

# ─── Role → Tool Policy (CLAUDE.md §14) ──────────────────────────────────────
_role_tool_policy := {
	"analyst": {"get_order", "get_customer"},
	"billing": {"get_order", "get_customer", "get_payment", "issue_refund"},
	"admin": {"get_order", "get_customer", "get_payment", "issue_refund", "delete_customer"},
}

# ─── Agent → Tool Capabilities (CLAUDE.md §4) ────────────────────────────────
_agent_tool_capability := {
	"order-agent": {"get_order", "get_customer"},
	"billing-agent": {"get_order", "get_payment", "issue_refund"},
	"admin-agent": {"get_customer", "delete_customer"},
	"supervisor": {},
}
