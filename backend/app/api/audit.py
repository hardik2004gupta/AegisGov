"""
Audit API — CLAUDE.md §19, Phase 4

Surfaces the PostgreSQL audit_events table via REST.

Contract:
    GET /api/v1/audit              — paginated list with filters
    GET /api/v1/audit/{trace_id}   — complete governance timeline for a trace
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import AuthenticatedUser, get_current_user
from app.db.models import AuditEvent
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])


# ─── Response models ──────────────────────────────────────────────────────────


class AuditEventResponse(BaseModel):
    id: str
    trace_id: str
    user_id: str
    agent_id: str
    action_type: str
    decision: str
    reason: Optional[str] = None
    payload: dict[str, Any]
    created_at: str


class AuditListResponse(BaseModel):
    items: list[AuditEventResponse]
    total: int
    limit: int
    offset: int


class TraceTimelineResponse(BaseModel):
    trace_id: str
    events: list[AuditEventResponse]
    summary: dict[str, Any]


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _event_to_response(e: AuditEvent) -> AuditEventResponse:
    return AuditEventResponse(
        id=str(e.id),
        trace_id=e.trace_id,
        user_id=e.user_id,
        agent_id=e.agent_id,
        action_type=e.action_type,
        decision=e.decision,
        reason=e.reason,
        payload=e.payload or {},
        created_at=e.created_at.isoformat() if e.created_at else "",
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("", response_model=AuditListResponse)
async def list_audit_events(
    trace_id: Optional[str] = Query(default=None, description="Filter by trace ID"),
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
    agent_id: Optional[str] = Query(default=None, description="Filter by agent ID"),
    decision: Optional[str] = Query(default=None, description="Filter by decision: ALLOWED, DENIED, BLOCKED, PENDING, APPROVED, REJECTED"),
    action_type: Optional[str] = Query(default=None, description="Filter by event type"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuditListResponse:
    """List audit events, newest first. Supports filtering and pagination."""
    base_q = select(AuditEvent)

    if trace_id:
        base_q = base_q.where(AuditEvent.trace_id == trace_id)
    if user_id:
        base_q = base_q.where(AuditEvent.user_id == user_id)
    if agent_id:
        base_q = base_q.where(AuditEvent.agent_id == agent_id)
    if decision:
        base_q = base_q.where(AuditEvent.decision == decision.upper())
    if action_type:
        base_q = base_q.where(AuditEvent.action_type == action_type.upper())

    # Total count before pagination
    count_q = select(func.count()).select_from(base_q.subquery())
    total: int = (await db.execute(count_q)).scalar() or 0

    # Paginated results
    page_q = base_q.order_by(AuditEvent.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(page_q)
    events = result.scalars().all()

    return AuditListResponse(
        items=[_event_to_response(e) for e in events],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{trace_id}", response_model=TraceTimelineResponse)
async def get_trace_timeline(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> TraceTimelineResponse:
    """Return a complete governance timeline for a single trace, oldest first."""
    result = await db.execute(
        select(AuditEvent)
        .where(AuditEvent.trace_id == trace_id)
        .order_by(AuditEvent.created_at.asc())
    )
    events = result.scalars().all()

    event_responses = [_event_to_response(e) for e in events]

    # Build a summary over all events in the trace
    all_decisions = [e.decision for e in events]
    all_users = list({e.user_id for e in events if e.user_id})
    all_agents = list({e.agent_id for e in events if e.agent_id})

    summary: dict[str, Any] = {
        "total_events": len(events),
        "final_decision": all_decisions[-1] if all_decisions else None,
        "user_ids": all_users,
        "agent_ids": all_agents,
        "started_at": events[0].created_at.isoformat() if events else None,
        "completed_at": events[-1].created_at.isoformat() if events else None,
        "decisions": {d: all_decisions.count(d) for d in set(all_decisions)},
    }

    return TraceTimelineResponse(
        trace_id=trace_id,
        events=event_responses,
        summary=summary,
    )
