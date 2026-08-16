"""
Central Audit Service — CLAUDE.md §8 Rule 8, Phase 4

Single interface for persisting governance events to audit_events.
Every governance decision — ALLOWED, DENIED, BLOCKED, PENDING — must be audited.
NEVER persist: JWT tokens, API keys, passwords, database credentials.

PostgreSQL is the system of record. Langfuse is optional observability only.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditEvent

logger = logging.getLogger(__name__)


# ─── Event type vocabulary ─────────────────────────────────────────────────────


class EventType:
    """action_type constants for audit_events rows."""

    IDENTITY_VERIFIED      = "IDENTITY_VERIFIED"
    IDENTITY_DENIED        = "IDENTITY_DENIED"
    INPUT_BLOCKED          = "INPUT_BLOCKED"
    INPUT_ACCEPTED         = "INPUT_ACCEPTED"
    AGENT_HANDOFF_ALLOWED  = "AGENT_HANDOFF_ALLOWED"
    AGENT_HANDOFF_DENIED   = "AGENT_HANDOFF_DENIED"
    TOOL_PROPOSAL_CREATED  = "TOOL_PROPOSAL_CREATED"
    TOOL_UNKNOWN           = "TOOL_UNKNOWN"
    TOOL_VALIDATION_DENIED = "TOOL_VALIDATION_DENIED"
    RUNTIME_LIMIT_BLOCKED  = "RUNTIME_LIMIT_BLOCKED"
    POLICY_ALLOWED         = "POLICY_ALLOWED"
    POLICY_DENIED          = "POLICY_DENIED"
    RISK_CLASSIFIED        = "RISK_CLASSIFIED"
    APPROVAL_CREATED       = "APPROVAL_CREATED"
    APPROVAL_APPROVED      = "APPROVAL_APPROVED"
    APPROVAL_REJECTED      = "APPROVAL_REJECTED"
    TOOL_EXECUTION_STARTED    = "TOOL_EXECUTION_STARTED"
    TOOL_EXECUTION_COMPLETED  = "TOOL_EXECUTION_COMPLETED"
    TOOL_EXECUTION_FAILED     = "TOOL_EXECUTION_FAILED"
    TOOL_RESULT_SANITIZED     = "TOOL_RESULT_SANITIZED"


class Decision:
    """decision constants — must match audit_events DB CHECK constraint."""

    ALLOWED  = "ALLOWED"
    DENIED   = "DENIED"
    BLOCKED  = "BLOCKED"
    PENDING  = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ─── Sensitive key filter ──────────────────────────────────────────────────────

_SENSITIVE_KEYS: frozenset[str] = frozenset({
    "authorization", "auth", "token", "jwt", "bearer",
    "password", "secret", "api_key", "apikey", "key",
    "database_url", "database_password", "credentials", "credential",
    "private_key", "access_token", "refresh_token", "client_secret",
})


def safe_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy of *data* with sensitive-looking keys removed."""
    return {k: v for k, v in data.items() if k.lower() not in _SENSITIVE_KEYS}


# ─── Audit Service ─────────────────────────────────────────────────────────────


class AuditService:
    """Central governance audit writer.

    All components call audit_service.record() rather than constructing
    AuditEvent rows directly. This keeps safe-serialization logic in one place.

    Never re-raises on failure: a failed audit write must not block an
    already-authorized action. Errors are logged prominently.
    """

    async def record(
        self,
        db: AsyncSession,
        *,
        trace_id: str,
        user_id: str,
        agent_id: str,
        action_type: str,
        decision: str,
        reason: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        try:
            event = AuditEvent(
                trace_id=trace_id,
                user_id=user_id,
                agent_id=agent_id,
                action_type=action_type,
                decision=decision,
                reason=reason[:2000] if reason else "",
                payload=safe_payload(payload or {}),
            )
            db.add(event)
            await db.commit()
        except Exception as exc:
            logger.error(
                "AUDIT WRITE FAILED action=%s trace_id=%s decision=%s: %s",
                action_type, trace_id, decision, exc,
            )


audit_service = AuditService()
