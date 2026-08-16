"""
Human-in-the-Loop Approval Endpoints — CLAUDE.md §15, §19

Implements the HITL approval workflow:
    GET  /api/v1/governance/approvals            — list approvals (filterable)
    GET  /api/v1/governance/approvals/{id}        — get specific approval
    POST /api/v1/governance/approvals/{id}/resolve — approve or reject

Security invariants enforced here:
    INVARIANT 2 — approver identity derived from JWT, never request body
    INVARIANT 8 — rejected approval MUST NOT result in DB mutation
    Single-use  — PENDING→APPROVED or PENDING→REJECTED only; no re-resolution

Only users with the 'admin' role may resolve approvals.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import AuthenticatedUser, get_current_user
from app.db.models import ApprovalRequest
from app.db.session import get_db
from app.governance.audit import Decision, EventType, audit_service
from app.governance.gateway import gateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/governance", tags=["governance"])


# ─── Response models ──────────────────────────────────────────────────────────


class ApprovalResponse(BaseModel):
    approval_id: str
    thread_id: str
    trace_id: Optional[str] = None
    agent_id: str
    user_id: str
    tool_name: str
    arguments: dict[str, Any]
    risk_level: str
    status: str
    approved_by: Optional[str] = None
    resolution_reason: Optional[str] = None
    created_at: str
    resolved_at: Optional[str] = None


class ResolveRequest(BaseModel):
    decision: Literal["APPROVED", "REJECTED"]
    resolution_reason: str = Field(min_length=1, max_length=1024)


class ResolveResponse(BaseModel):
    approval_id: str
    decision: str
    tool_name: str
    execution_result: Optional[dict[str, Any]] = None
    message: str


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _approval_to_response(a: ApprovalRequest) -> ApprovalResponse:
    return ApprovalResponse(
        approval_id=str(a.id),
        thread_id=a.thread_id,
        trace_id=a.trace_id,
        agent_id=a.agent_id,
        user_id=a.user_id,
        tool_name=a.tool_name,
        arguments=a.arguments or {},
        risk_level=a.risk_level,
        status=a.status,
        approved_by=a.approved_by,
        resolution_reason=a.resolution_reason,
        created_at=a.created_at.isoformat() if a.created_at else "",
        resolved_at=a.resolved_at.isoformat() if a.resolved_at else None,
    )


def _require_admin(user: AuthenticatedUser) -> None:
    """Fail with 403 if the user is not an admin (INVARIANT 2 — JWT-derived only)."""
    if "admin" not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users with the 'admin' role may resolve approvals.",
        )


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/approvals", response_model=list[ApprovalResponse])
async def list_approvals(
    pending_only: bool = Query(default=True, description="When true, return only PENDING approvals"),
    approval_status: Optional[str] = Query(default=None, alias="status", description="Filter by status: PENDING, APPROVED, REJECTED"),
    risk_level: Optional[str] = Query(default=None, description="Filter by risk level: LOW, MEDIUM, HIGH, CRITICAL"),
    agent_id: Optional[str] = Query(default=None, description="Filter by agent ID"),
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[ApprovalResponse]:
    """List approval requests, newest first.

    By default returns only PENDING approvals (those awaiting review).
    Use status= to filter by a specific status, or pending_only=false for all.
    """
    q = select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc()).limit(limit)

    if approval_status:
        q = q.where(ApprovalRequest.status == approval_status.upper())
    elif pending_only:
        q = q.where(ApprovalRequest.status == "PENDING")

    if risk_level:
        q = q.where(ApprovalRequest.risk_level == risk_level.upper())
    if agent_id:
        q = q.where(ApprovalRequest.agent_id == agent_id)
    if user_id:
        q = q.where(ApprovalRequest.user_id == user_id)

    result = await db.execute(q)
    approvals = result.scalars().all()
    return [_approval_to_response(a) for a in approvals]


@router.get("/approvals/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    approval_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ApprovalResponse:
    """Get a specific approval request by ID."""
    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval {approval_id} not found.",
        )
    return _approval_to_response(approval)


@router.post("/approvals/{approval_id}/resolve", response_model=ResolveResponse)
async def resolve_approval(
    approval_id: UUID,
    body: ResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ResolveResponse:
    """Approve or reject a pending HITL action.

    INVARIANT 2: Approver identity is taken from the JWT — never from request body.
    INVARIANT 8: REJECTED decision results in NO database mutations to business data.
    Single-use: an already-resolved approval cannot be re-resolved.
    Requires admin role.
    """
    _require_admin(current_user)

    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval {approval_id} not found.",
        )

    # Single-use enforcement: only PENDING approvals may be resolved
    if approval.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Approval {approval_id} is already {approval.status}. Cannot re-resolve.",
        )

    approver_id = current_user.user_id
    trace_id = approval.trace_id or f"approval:{approval.id}"
    now = datetime.now(timezone.utc)

    # ── REJECTED: INVARIANT 8 — no business data mutations ───────────────────
    if body.decision == "REJECTED":
        approval.status = "REJECTED"
        approval.approved_by = approver_id
        approval.resolution_reason = body.resolution_reason
        approval.resolved_at = now
        await db.commit()

        await audit_service.record(
            db,
            trace_id=trace_id,
            user_id=approval.user_id,
            agent_id=approval.agent_id,
            action_type=EventType.APPROVAL_REJECTED,
            decision=Decision.REJECTED,
            reason=f"Rejected by {approver_id}: {body.resolution_reason}",
            payload={
                "tool": approval.tool_name,
                "approval_id": str(approval.id),
                "approver": approver_id,
                "risk": approval.risk_level,
            },
        )

        logger.info(
            "Approval REJECTED approval_id=%s tool=%s by=%s",
            approval_id, approval.tool_name, approver_id,
        )

        return ResolveResponse(
            approval_id=str(approval_id),
            decision="REJECTED",
            tool_name=approval.tool_name,
            execution_result=None,
            message="Action rejected. No database mutations occurred.",
        )

    # ── APPROVED: re-validate, then execute ──────────────────────────────────
    approval.status = "APPROVED"
    approval.approved_by = approver_id
    approval.resolution_reason = body.resolution_reason
    approval.resolved_at = now
    await db.commit()

    await audit_service.record(
        db,
        trace_id=trace_id,
        user_id=approval.user_id,
        agent_id=approval.agent_id,
        action_type=EventType.APPROVAL_APPROVED,
        decision=Decision.APPROVED,
        reason=f"Approved by {approver_id}: {body.resolution_reason}",
        payload={
            "tool": approval.tool_name,
            "approval_id": str(approval.id),
            "approver": approver_id,
            "risk": approval.risk_level,
        },
    )

    logger.info(
        "Approval APPROVED approval_id=%s tool=%s by=%s",
        approval_id, approval.tool_name, approver_id,
    )

    try:
        execution_result = await gateway.execute_approved_action(
            approval=approval,
            db=db,
            approver_id=approver_id,
        )
    except ValueError as exc:
        logger.error(
            "Approved action execution failed approval_id=%s: %s",
            approval_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Execution failed after approval: {exc}",
        ) from exc
    except Exception as exc:
        logger.error(
            "Unexpected error executing approved action approval_id=%s: %s",
            approval_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Execution error after approval.",
        ) from exc

    return ResolveResponse(
        approval_id=str(approval_id),
        decision="APPROVED",
        tool_name=approval.tool_name,
        execution_result=execution_result,
        message="Approved and executed successfully.",
    )
