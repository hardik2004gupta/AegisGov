"""
POST /api/v1/agent/run

The primary agent execution endpoint.

INVARIANT 2 (CLAUDE.md §26): Authorization derives exclusively from the
verified Keycloak JWT. Role/identity claims in the request body are ignored.

Phase 2 response status: PROPOSAL_READY, DENIED, BLOCKED, FAILED.
No tool is executed in Phase 2; the response contains a structured proposal.

Phase 3 will add: COMPLETED, INTERRUPTED_PENDING_APPROVAL.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.identity import AuthenticatedUser, get_current_user
from app.core.security import ToolProposal
from app.graph.state import AegisState, initial_state
from app.graph.workflow import compiled_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


# ─── Request / Response models ────────────────────────────────────────────────


class AgentRunRequest(BaseModel):
    thread_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4096)
    # INVARIANT 2: no 'role', 'user_id', or identity fields accepted here


class GovernanceInfo(BaseModel):
    identity_verified: bool
    policy_decision: str
    agent_id: Optional[str] = None
    agent_spiffe_id: Optional[str] = None


class AgentRunResponse(BaseModel):
    thread_id: str
    status: str
    trace_id: str
    output: Optional[str] = None
    error: Optional[str] = None
    agent: Optional[dict[str, Any]] = None
    proposal: Optional[dict[str, Any]] = None
    governance: GovernanceInfo


# ─── Endpoint ─────────────────────────────────────────────────────────────────


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    body: AgentRunRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AgentRunResponse:
    """Submit a message to the AegisGov agent runtime.

    Identity is taken exclusively from the verified Keycloak JWT.
    Any identity or role claims in the request body are silently ignored.
    """
    state = initial_state(
        thread_id=body.thread_id,
        user_id=current_user.user_id,
        username=current_user.username,
        user_roles=current_user.roles,
        message=body.message,
    )

    logger.info(
        "Agent run started user=%s roles=%s thread_id=%s trace_id=%s",
        current_user.username,
        current_user.roles,
        body.thread_id,
        state["trace_id"],
    )

    try:
        result: AegisState = await compiled_graph.ainvoke(state)
    except Exception as exc:
        logger.error("Graph execution failed trace_id=%s: %s", state["trace_id"], exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent runtime error",
        ) from exc

    return _build_response(result)


def _build_response(result: AegisState) -> AgentRunResponse:
    run_status = result.get("status", "FAILED")

    proposal: Optional[dict[str, Any]] = None
    if result.get("proposed_tool"):
        proposal = {
            "tool": result["proposed_tool"],
            "arguments": result.get("tool_arguments") or {},
            "reason": result.get("proposal_reason"),
        }

    agent_info: Optional[dict[str, Any]] = None
    if result.get("agent_id") and result["agent_id"] != "supervisor":
        agent_info = {
            "id": result["agent_id"],
            "spiffe_id": result.get("agent_spiffe_id"),
            "capabilities": result.get("agent_capabilities", []),
        }

    governance = GovernanceInfo(
        identity_verified=True,  # guaranteed by get_current_user dependency
        policy_decision=result.get("governance_status", "UNKNOWN"),
        agent_id=result.get("agent_id"),
        agent_spiffe_id=result.get("agent_spiffe_id"),
    )

    return AgentRunResponse(
        thread_id=result["thread_id"],
        status=run_status,
        trace_id=result["trace_id"],
        output=result.get("output"),
        error=result.get("error"),
        agent=agent_info,
        proposal=proposal,
        governance=governance,
    )
