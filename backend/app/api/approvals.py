# Phase 4: Approval CRUD + resolve
#
# This module implements the human-in-the-loop approval endpoints.
# Full implementation in Phase 4, after Phase 3 establishes HITL flow.
#
# Contract (CLAUDE.md §19):
#   GET  /api/v1/governance/approvals
#   GET  /api/v1/governance/approvals/{approval_id}
#   POST /api/v1/governance/approvals/{approval_id}/resolve
#     Body: { "decision": "APPROVED"|"REJECTED", "resolution_reason": str }

from fastapi import APIRouter

router = APIRouter(prefix="/governance", tags=["governance"])

# TODO Phase 4: implement approval list, get, and resolve endpoints
