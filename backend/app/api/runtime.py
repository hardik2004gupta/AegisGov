"""
Runtime Status API — CLAUDE.md §19, Phase 4

Exposes aggregate governance metrics derived from PostgreSQL:
    GET /api/v1/runtime/status

Shows decision counts, approval statistics, and configured limits.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.identity import AuthenticatedUser, get_current_user
from app.db.models import ApprovalRequest, AuditEvent
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/status")
async def runtime_status(
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Return aggregate runtime metrics from PostgreSQL.

    Decision counts are derived from audit_events; approval counts from
    approval_requests. Both reflect all-time totals since the last DB reset.
    """
    # Decision counts from audit_events
    decision_counts: dict[str, int] = {}
    for decision in ("ALLOWED", "DENIED", "BLOCKED"):
        count = (
            await db.execute(
                select(func.count(AuditEvent.id)).where(AuditEvent.decision == decision)
            )
        ).scalar() or 0
        decision_counts[decision.lower()] = int(count)

    # Approval status counts
    approval_counts: dict[str, int] = {}
    for status in ("PENDING", "APPROVED", "REJECTED"):
        count = (
            await db.execute(
                select(func.count(ApprovalRequest.id)).where(ApprovalRequest.status == status)
            )
        ).scalar() or 0
        approval_counts[status.lower()] = int(count)

    total_decisions = sum(decision_counts.values())

    return {
        "summary": {
            "total_decisions": total_decisions,
            "allowed": decision_counts.get("allowed", 0),
            "denied": decision_counts.get("denied", 0),
            "blocked": decision_counts.get("blocked", 0),
            "pending_approvals": approval_counts.get("pending", 0),
        },
        "approvals": approval_counts,
        "limits": {
            "max_tool_calls": settings.max_tool_calls,
            "max_execution_time_seconds": settings.max_execution_time_seconds,
            "max_agent_handoffs": settings.max_agent_handoffs,
            "max_identical_tool_calls": settings.max_identical_tool_calls,
        },
    }
