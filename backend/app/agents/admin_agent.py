# Phase 2: Admin Agent
#
# Specialist agent for administrative operations.
# Tools (CLAUDE.md §4): get_customer, delete_customer
# Workload identity: aegis://agents/admin-agent
#
# Authorized by admin role ONLY.
# delete_customer is CRITICAL risk — always requires human approval.

from __future__ import annotations

# TODO Phase 2: implement admin agent node for LangGraph workflow
