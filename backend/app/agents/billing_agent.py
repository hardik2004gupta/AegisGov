# Phase 2: Billing Agent
#
# Specialist agent for payment and refund operations.
# Tools (CLAUDE.md §4): get_order, get_payment, issue_refund
# Workload identity: aegis://agents/billing-agent
#
# Authorized by billing and admin roles only.
# issue_refund > $500 requires human approval (HITL).

from __future__ import annotations

# TODO Phase 2: implement billing agent node for LangGraph workflow
