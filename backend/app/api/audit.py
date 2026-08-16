# Phase 4: Audit event queries
#
# This module surfaces the PostgreSQL audit_events table via REST.
# Full implementation in Phase 4.
#
# Contract (CLAUDE.md §19):
#   GET /api/v1/audit
#   GET /api/v1/audit/{trace_id}

from fastapi import APIRouter

router = APIRouter(prefix="/audit", tags=["audit"])

# TODO Phase 4: implement audit list and trace-lookup endpoints
