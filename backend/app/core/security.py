"""
Agent Identity & Request Context

CLAUDE.md §5 — Agent Identity:
    Each agent has a distinct workload identity URI:
        aegis://agents/supervisor
        aegis://agents/order-agent
        aegis://agents/billing-agent
        aegis://agents/admin-agent

    The MVP represents workload identity with signed internal JWTs.
    Architecture is extensible toward SPIFFE/SVID in future phases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import jwt
from pydantic import BaseModel

from app.core.config import settings

AgentType = Literal["supervisor", "specialist"]


# ─── Agent capabilities (CLAUDE.md §4) ───────────────────────────────────────

AGENT_CAPABILITIES: dict[str, list[str]] = {
    "supervisor": [],  # routes only; never executes tools directly
    "order-agent": ["get_order", "get_customer"],
    "billing-agent": ["get_order", "get_payment", "issue_refund"],
    "admin-agent": ["get_customer", "delete_customer"],
}


# ─── Agent Identity ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AgentIdentity:
    """Workload identity for an AegisGov agent."""

    agent_id: str
    spiffe_id: str
    agent_type: AgentType
    capabilities: list[str] = field(default_factory=list)

    def to_workload_jwt(self) -> str:
        """Issue a short-lived signed workload JWT for this agent."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": self.spiffe_id,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        return jwt.encode(
            payload,
            settings.agent_jwt_secret,
            algorithm=settings.agent_jwt_algorithm,
        )


# ─── Canonical workload identities (CLAUDE.md §5) ────────────────────────────

SUPERVISOR_IDENTITY = AgentIdentity(
    agent_id="supervisor",
    spiffe_id="aegis://agents/supervisor",
    agent_type="supervisor",
    capabilities=AGENT_CAPABILITIES["supervisor"],
)

ORDER_AGENT_IDENTITY = AgentIdentity(
    agent_id="order-agent",
    spiffe_id="aegis://agents/order-agent",
    agent_type="specialist",
    capabilities=AGENT_CAPABILITIES["order-agent"],
)

BILLING_AGENT_IDENTITY = AgentIdentity(
    agent_id="billing-agent",
    spiffe_id="aegis://agents/billing-agent",
    agent_type="specialist",
    capabilities=AGENT_CAPABILITIES["billing-agent"],
)

ADMIN_AGENT_IDENTITY = AgentIdentity(
    agent_id="admin-agent",
    spiffe_id="aegis://agents/admin-agent",
    agent_type="specialist",
    capabilities=AGENT_CAPABILITIES["admin-agent"],
)

AGENT_REGISTRY: dict[str, AgentIdentity] = {
    identity.agent_id: identity
    for identity in (
        SUPERVISOR_IDENTITY,
        ORDER_AGENT_IDENTITY,
        BILLING_AGENT_IDENTITY,
        ADMIN_AGENT_IDENTITY,
    )
}


# ─── Request Context ──────────────────────────────────────────────────────────


@dataclass
class RequestContext:
    """Dual-identity context that flows through the full execution pipeline.

    Human Identity + Agent Identity = Authorization Context (CLAUDE.md §5).
    Phase 3 will pass this into OPA for policy decisions.
    """

    user_id: str
    username: str
    user_roles: list[str]
    agent: AgentIdentity | None
    thread_id: str
    trace_id: str


# ─── Tool Proposal ────────────────────────────────────────────────────────────


class ToolProposal(BaseModel):
    """Structured proposal output from a specialist agent.

    Agents produce proposals; the Secure Tool Gateway executes them (Phase 3).
    INVARIANT 1 (CLAUDE.md §26): Direct Agent→Tool execution is FORBIDDEN.
    """

    tool_name: str
    arguments: dict
    agent_id: str
    agent_spiffe_id: str
    thread_id: str
    reason: str
