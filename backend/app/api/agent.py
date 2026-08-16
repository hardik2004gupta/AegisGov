# Phase 4: POST /api/v1/agent/run
#
# This module implements the primary agent execution endpoint.
# The full implementation lands in Phase 4 after:
#   - Phase 2: Identity verification + LangGraph runtime
#   - Phase 3: Secure Tool Gateway + OPA + HITL
#
# Contract (CLAUDE.md §19):
#   POST /api/v1/agent/run
#   Authorization: Bearer <Keycloak JWT>
#   Body: { "thread_id": str, "message": str }
#   Response: { thread_id, status, trace_id, output, governance }

from fastapi import APIRouter

router = APIRouter(prefix="/agent", tags=["agent"])

# TODO Phase 4: implement /run endpoint
