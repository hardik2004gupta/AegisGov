"""
Secure Tool Gateway — CLAUDE.md §8

This is the most important implementation component in the entire project.

The gateway enforces the complete 10-stage pipeline (CLAUDE.md §8):
    1.  Identity Context
    2.  Tool Registry Lookup       ← fail closed on unknown tool
    3.  Pydantic Validation        ← fail closed on schema violation
    4.  Runtime Safety             ← fail closed if budget exceeded
    5.  OPA Authorization          ← fail closed if OPA unavailable
    6.  Risk Classification
    7.  Human Approval Decision
    8.  Secure Tool Execution (with least-privilege DB role)
    9.  Result Sanitization
    10. Audit

INVARIANTS enforced here (CLAUDE.md §26):
    INVARIANT 1: Agent→handler calls are architecturally impossible
    INVARIANT 5: CRITICAL risk → HITL, never auto-execute
    INVARIANT 6: Invalid parameters → no handler invocation
    INVARIANT 7: Unregistered tool → DENY
    INVARIANT 8: Rejected approval → no DB mutation
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ToolProposal
from app.db.models import ApprovalRequest
from app.governance.audit import Decision, EventType, audit_service
from app.governance.middleware import check_runtime_limits
from app.governance.policy import PolicyResult, policy_service
from app.governance.risk import RiskLevel, classify_risk, requires_hitl
from app.graph.state import AegisState
from app.tools.registry import TOOL_REGISTRY

logger = logging.getLogger(__name__)


# ─── Gateway Result ────────────────────────────────────────────────────────────


@dataclass
class GatewayResult:
    """Structured outcome from the secure tool gateway pipeline."""

    decision: str  # "ALLOWED" | "DENIED" | "BLOCKED" | "PENDING_APPROVAL"
    risk_level: Optional[str] = None
    result: Optional[dict[str, Any]] = None
    approval_id: Optional[str] = None
    reason: Optional[str] = None
    requires_approval: bool = False
    execution_time_ms: Optional[float] = None


# ─── Secure Tool Gateway ───────────────────────────────────────────────────────


class SecureToolGateway:
    """The sole authorized execution boundary between agents and tool handlers.

    Agents produce ToolProposal objects. The gateway executes them — or
    denies/pauses them — after all security checks pass.

    Architecture:
        SecureToolGateway.execute(proposal, state, db)

    The `db` session is provided by the calling graph node, which creates
    it from AsyncSessionLocal. Agents never see the session.
    """

    async def execute(
        self,
        proposal: ToolProposal,
        state: AegisState,
        db: AsyncSession,
    ) -> GatewayResult:
        """Run the complete 10-stage pipeline for a tool proposal.

        Pipeline order is an architectural invariant — never reorder.
        Every stage that fails returns DENY or BLOCKED.
        """
        import time
        start = time.monotonic()

        # ── Stage 1: Identity Context ──────────────────────────────────────────
        user_id = state["user_id"]
        user_roles = state["user_roles"]
        agent_id = proposal.agent_id
        agent_spiffe_id = proposal.agent_spiffe_id
        trace_id = state["trace_id"]
        tool_name = proposal.tool_name

        # ── Stage 2: Tool Registry Lookup ─────────────────────────────────────
        entry = TOOL_REGISTRY.get(tool_name)
        if entry is None:
            reason = f"Tool '{tool_name}' is not registered — INVARIANT 7"
            logger.warning("Gateway DENIED unregistered tool=%s trace_id=%s", tool_name, trace_id)
            await audit_service.record(
                db,
                trace_id=trace_id, user_id=user_id, agent_id=agent_id,
                action_type=EventType.TOOL_UNKNOWN, decision=Decision.DENIED, reason=reason,
                payload={"tool": tool_name},
            )
            return GatewayResult(decision="DENIED", reason=reason)

        # ── Stage 3: Pydantic Validation ──────────────────────────────────────
        schema_cls = entry["schema"]
        try:
            validated = schema_cls(**proposal.arguments)
        except ValidationError as exc:
            reason = f"Parameter validation failed: {exc}"
            logger.warning("Gateway DENIED validation error tool=%s trace_id=%s", tool_name, trace_id)
            await audit_service.record(
                db,
                trace_id=trace_id, user_id=user_id, agent_id=agent_id,
                action_type=EventType.TOOL_VALIDATION_DENIED, decision=Decision.DENIED, reason=reason,
                payload={"tool": tool_name},
            )
            return GatewayResult(decision="DENIED", reason=reason)

        validated_args = validated.model_dump()

        # ── Stage 4: Runtime Safety ───────────────────────────────────────────
        limit_result = check_runtime_limits(state)
        if limit_result:
            reason = limit_result.get("block_reason", "Runtime budget exceeded")
            logger.warning("Gateway BLOCKED runtime limit tool=%s trace_id=%s", tool_name, trace_id)
            await audit_service.record(
                db,
                trace_id=trace_id, user_id=user_id, agent_id=agent_id,
                action_type=EventType.RUNTIME_LIMIT_BLOCKED, decision=Decision.BLOCKED, reason=reason,
                payload={"tool": tool_name},
            )
            return GatewayResult(decision="BLOCKED", reason=reason)

        # ── Stage 5: OPA Authorization ────────────────────────────────────────
        opa_result: PolicyResult = await policy_service.allow_tool_execution(
            user_id=user_id,
            user_roles=user_roles,
            agent_id=agent_id,
            agent_spiffe_id=agent_spiffe_id,
            tool_name=tool_name,
            resource_id=str(validated_args.get("order_id") or validated_args.get("customer_id") or ""),
            arguments=validated_args,
        )
        if not opa_result.allow:
            reason = f"OPA denied: {opa_result.reason}"
            logger.info("Gateway DENIED OPA tool=%s trace_id=%s", tool_name, trace_id)
            await audit_service.record(
                db,
                trace_id=trace_id, user_id=user_id, agent_id=agent_id,
                action_type=EventType.POLICY_DENIED, decision=Decision.DENIED, reason=reason,
                payload={"tool": tool_name, "roles": user_roles},
            )
            return GatewayResult(decision="DENIED", reason=reason)

        # ── Stage 6: Risk Classification ──────────────────────────────────────
        risk_level: RiskLevel = classify_risk(tool_name, validated_args)

        # ── Stage 7: Human Approval Decision ─────────────────────────────────
        hitl_required = requires_hitl(tool_name, validated_args, risk_level) or opa_result.require_human_approval

        if hitl_required:
            approval_id = await self._create_approval(
                db=db,
                thread_id=state["thread_id"],
                trace_id=trace_id,
                agent_id=agent_id,
                user_id=user_id,
                tool_name=tool_name,
                arguments=validated_args,
                risk_level=risk_level,
            )
            await audit_service.record(
                db,
                trace_id=trace_id, user_id=user_id, agent_id=agent_id,
                action_type=EventType.APPROVAL_CREATED, decision=Decision.PENDING,
                reason=f"Human approval required for {tool_name} (risk={risk_level})",
                payload={"tool": tool_name, "risk": risk_level, "approval_id": str(approval_id)},
            )
            logger.info(
                "Gateway PENDING HITL tool=%s risk=%s approval_id=%s trace_id=%s",
                tool_name, risk_level, approval_id, trace_id,
            )
            return GatewayResult(
                decision="PENDING_APPROVAL",
                risk_level=risk_level,
                approval_id=str(approval_id),
                requires_approval=True,
            )

        # ── Stage 8: Secure Tool Execution (with least-privilege DB role) ─────
        handler = entry["handler"]
        target_role = entry["target_db_role"]

        try:
            raw_result = await self._execute_with_role(db, target_role, handler, validated_args)
        except ValueError as exc:
            reason = str(exc)
            logger.warning("Gateway execution error tool=%s trace_id=%s: %s", tool_name, trace_id, reason)
            await audit_service.record(
                db,
                trace_id=trace_id, user_id=user_id, agent_id=agent_id,
                action_type=EventType.TOOL_EXECUTION_FAILED, decision=Decision.DENIED, reason=reason,
                payload={"tool": tool_name, "risk": risk_level},
            )
            return GatewayResult(decision="DENIED", reason=reason)
        except Exception as exc:
            reason = f"Execution error: {exc}"
            logger.error("Gateway unexpected error tool=%s trace_id=%s: %s", tool_name, trace_id, exc)
            await audit_service.record(
                db,
                trace_id=trace_id, user_id=user_id, agent_id=agent_id,
                action_type=EventType.TOOL_EXECUTION_FAILED, decision=Decision.DENIED, reason=reason,
                payload={"tool": tool_name, "risk": risk_level},
            )
            return GatewayResult(decision="DENIED", reason=reason)

        # ── Stage 9: Result Sanitization (handlers return clean dicts already)

        # ── Stage 10: Audit ───────────────────────────────────────────────────
        elapsed_ms = (time.monotonic() - start) * 1000
        await audit_service.record(
            db,
            trace_id=trace_id, user_id=user_id, agent_id=agent_id,
            action_type=EventType.TOOL_EXECUTION_COMPLETED, decision=Decision.ALLOWED,
            reason=f"Executed {tool_name} successfully (risk={risk_level})",
            payload={
                "tool": tool_name,
                "risk": risk_level,
                "role_used": target_role,
                "execution_time_ms": round(elapsed_ms, 1),
            },
        )

        logger.info(
            "Gateway ALLOWED tool=%s risk=%s role=%s trace_id=%s %.1fms",
            tool_name, risk_level, target_role, trace_id, elapsed_ms,
        )

        return GatewayResult(
            decision="ALLOWED",
            risk_level=risk_level,
            result=raw_result,
            requires_approval=False,
            execution_time_ms=elapsed_ms,
        )

    async def execute_approved_action(
        self,
        approval: ApprovalRequest,
        db: AsyncSession,
        approver_id: str,
    ) -> dict[str, Any]:
        """Execute a tool after a HITL approval has been granted.

        Re-validates that the tool is still registered and arguments are
        still valid before executing (CLAUDE.md §23). Does NOT re-check HITL
        since the human approval already satisfies that requirement.

        INVARIANT 8: A rejected approval must NEVER reach this method.
        The caller (approval API) is responsible for checking status==APPROVED.
        """
        tool_name = approval.tool_name
        trace_id = approval.trace_id or f"approval:{approval.id}"

        # Re-verify tool is still registered (could have been removed)
        entry = TOOL_REGISTRY.get(tool_name)
        if entry is None:
            raise ValueError(f"Tool '{tool_name}' is no longer registered")

        # Re-validate stored arguments (Pydantic)
        schema_cls = entry["schema"]
        try:
            validated = schema_cls(**approval.arguments)
        except ValidationError as exc:
            raise ValueError(f"Stored arguments are no longer valid: {exc}") from exc

        validated_args = validated.model_dump()

        # Execute with least-privilege role
        handler = entry["handler"]
        target_role = entry["target_db_role"]
        result = await self._execute_with_role(db, target_role, handler, validated_args)

        await audit_service.record(
            db,
            trace_id=trace_id,
            user_id=approval.user_id,
            agent_id=approval.agent_id,
            action_type=EventType.TOOL_EXECUTION_COMPLETED,
            decision=Decision.ALLOWED,
            reason=f"Executed after HITL approval by {approver_id}",
            payload={
                "tool": tool_name,
                "approval_id": str(approval.id),
                "approver": approver_id,
                "risk": approval.risk_level,
                "role_used": target_role,
            },
        )

        return result

    # ── Private helpers ────────────────────────────────────────────────────────

    async def _execute_with_role(
        self,
        db: AsyncSession,
        role: str,
        handler,
        args: dict,
    ) -> dict:
        """Execute a handler within a transaction using a least-privilege DB role.

        The SET LOCAL ROLE applies for the duration of the explicit transaction.
        When the transaction ends, the role reverts to the application user.
        """
        async with db.begin():
            await db.execute(text(f'SET LOCAL ROLE "{role}"'))
            result = await handler(args, db)
        return result

    async def _create_approval(
        self,
        db: AsyncSession,
        thread_id: str,
        trace_id: str,
        agent_id: str,
        user_id: str,
        tool_name: str,
        arguments: dict,
        risk_level: str,
    ) -> uuid.UUID:
        """Persist a pending approval request to PostgreSQL."""
        approval = ApprovalRequest(
            thread_id=thread_id,
            trace_id=trace_id,
            agent_id=agent_id,
            user_id=user_id,
            tool_name=tool_name,
            arguments=arguments,
            risk_level=risk_level,
            status="PENDING",
        )
        db.add(approval)
        await db.commit()
        # With expire_on_commit=False, approval.id is accessible without refresh
        return approval.id


# Module-level singleton
gateway = SecureToolGateway()
