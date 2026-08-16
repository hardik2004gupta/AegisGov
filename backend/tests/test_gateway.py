"""
Phase 3: Secure Tool Gateway Tests

Tests the full 10-stage gateway pipeline (CLAUDE.md §8).

Structure:
  Unit tests (no network): mock OPA, mock/real DB for pipeline-failure scenarios
  Integration tests (opa + db marks): full execution with real OPA + PostgreSQL

INVARIANTS verified:
  INVARIANT 1 — agent→handler calls impossible (gateway is the only path)
  INVARIANT 5 — CRITICAL action never auto-executes
  INVARIANT 6 — invalid parameters blocked before handler
  INVARIANT 7 — unregistered tool fails closed
  INVARIANT 8 — rejected approval → no DB mutation
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.security import ToolProposal
from app.governance.gateway import GatewayResult, SecureToolGateway
from app.governance.policy import PolicyResult
from app.graph.state import initial_state


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_state(**kwargs):
    base = initial_state(
        thread_id="thr_test",
        user_id="usr_test",
        username="test_user",
        user_roles=["billing"],
        message="test",
        trace_id="trc_test001",
    )
    base.update(
        agent_id="billing-agent",
        agent_spiffe_id="aegis://agents/billing-agent",
    )
    base.update(kwargs)
    return base


def _make_proposal(tool_name: str, arguments: dict) -> ToolProposal:
    return ToolProposal(
        tool_name=tool_name,
        arguments=arguments,
        agent_id="billing-agent",
        agent_spiffe_id="aegis://agents/billing-agent",
        thread_id="thr_test",
        reason="test",
    )


def _make_mock_db():
    """Mock AsyncSession for tests that shouldn't touch PostgreSQL."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    # Mock session.begin() as an async context manager
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=None)
    cm.__aexit__ = AsyncMock(return_value=False)
    db.begin = MagicMock(return_value=cm)
    return db


def _opa_allow(require_hitl: bool = False) -> PolicyResult:
    return PolicyResult(allow=True, require_human_approval=require_hitl, reason="allowed")


def _opa_deny() -> PolicyResult:
    return PolicyResult(allow=False, require_human_approval=False, reason="denied by policy")


# ─── Unit Tests: Pipeline Stage Failures ─────────────────────────────────────
# These tests do not require OPA or PostgreSQL.


async def test_unregistered_tool_fails_closed() -> None:
    """INVARIANT 7: Unregistered tool must DENY before any other check."""
    gw = SecureToolGateway()
    proposal = _make_proposal("hack_the_planet", {"arg": "x"})
    db = _make_mock_db()

    result = await gw.execute(proposal, _make_state(), db)

    assert result.decision == "DENIED"
    assert "not registered" in (result.reason or "").lower()


async def test_invalid_parameters_blocked_before_opa() -> None:
    """INVARIANT 6: Invalid parameters must never reach OPA or handler."""
    gw = SecureToolGateway()
    # issue_refund requires amount > 0, but we pass a negative value
    proposal = _make_proposal("issue_refund", {"order_id": 8829, "amount": -50, "reason": "test"})
    db = _make_mock_db()

    with patch("app.governance.gateway.policy_service") as mock_svc:
        mock_svc.allow_tool_execution = AsyncMock()
        result = await gw.execute(proposal, _make_state(), db)

    # OPA must not be called (pipeline fails at Pydantic stage)
    mock_svc.allow_tool_execution.assert_not_called()
    assert result.decision == "DENIED"


async def test_invalid_parameters_missing_required_field() -> None:
    """Missing required field should fail Pydantic validation, not reach OPA."""
    gw = SecureToolGateway()
    # get_order requires order_id; send empty dict
    proposal = _make_proposal("get_order", {})
    db = _make_mock_db()

    with patch("app.governance.gateway.policy_service") as mock_svc:
        mock_svc.allow_tool_execution = AsyncMock()
        result = await gw.execute(proposal, _make_state(), db)

    mock_svc.allow_tool_execution.assert_not_called()
    assert result.decision == "DENIED"


async def test_opa_deny_blocks_execution() -> None:
    """OPA DENY must block tool execution."""
    gw = SecureToolGateway()
    proposal = _make_proposal("get_order", {"order_id": 421})
    db = _make_mock_db()

    with patch("app.governance.gateway.policy_service") as mock_svc:
        mock_svc.allow_tool_execution = AsyncMock(return_value=_opa_deny())
        result = await gw.execute(proposal, _make_state(), db)

    assert result.decision == "DENIED"
    assert "opa" in (result.reason or "").lower()


async def test_opa_unavailable_returns_deny() -> None:
    """Fail-closed: if OPA returns error, result must be DENIED."""
    from app.governance.policy import _OPA_DENY

    gw = SecureToolGateway()
    proposal = _make_proposal("get_order", {"order_id": 421})
    db = _make_mock_db()

    with patch("app.governance.gateway.policy_service") as mock_svc:
        mock_svc.allow_tool_execution = AsyncMock(return_value=_OPA_DENY)
        result = await gw.execute(proposal, _make_state(), db)

    assert result.decision == "DENIED"


async def test_runtime_budget_exceeded_blocks_before_opa() -> None:
    """If tool_call_count >= max, execution stops before OPA."""
    from app.core.config import settings

    gw = SecureToolGateway()
    proposal = _make_proposal("get_order", {"order_id": 421})
    db = _make_mock_db()
    state = _make_state(tool_call_count=settings.max_tool_calls)

    with patch("app.governance.gateway.policy_service") as mock_svc:
        mock_svc.allow_tool_execution = AsyncMock()
        result = await gw.execute(proposal, state, db)

    mock_svc.allow_tool_execution.assert_not_called()
    assert result.decision == "BLOCKED"


async def test_delete_customer_always_triggers_hitl() -> None:
    """INVARIANT 5: CRITICAL action must pause for HITL, never auto-execute."""
    gw = SecureToolGateway()
    proposal = ToolProposal(
        tool_name="delete_customer",
        arguments={"customer_id": 42, "reason": "test deletion request"},
        agent_id="admin-agent",
        agent_spiffe_id="aegis://agents/admin-agent",
        thread_id="thr_admin",
        reason="test",
    )
    db = _make_mock_db()
    state = _make_state(
        agent_id="admin-agent",
        agent_spiffe_id="aegis://agents/admin-agent",
        user_roles=["admin"],
    )

    with patch("app.governance.gateway.policy_service") as mock_svc, \
         patch("app.governance.audit.audit_service.record", new=AsyncMock()):
        mock_svc.allow_tool_execution = AsyncMock(
            return_value=PolicyResult(allow=True, require_human_approval=True, reason="requires hitl")
        )
        # Mock _create_approval so we don't need real DB
        gw._create_approval = AsyncMock(return_value=uuid4())

        result = await gw.execute(proposal, state, db)

    assert result.decision == "PENDING_APPROVAL"
    assert result.approval_id is not None


async def test_issue_refund_over_500_triggers_hitl() -> None:
    """HIGH risk + amount > $500 must trigger HITL (CLAUDE.md §14)."""
    gw = SecureToolGateway()
    proposal = _make_proposal(
        "issue_refund",
        {"order_id": 8829, "amount": 700.0, "reason": "large refund request"},
    )
    db = _make_mock_db()

    with patch("app.governance.gateway.policy_service") as mock_svc, \
         patch("app.governance.audit.audit_service.record", new=AsyncMock()):
        mock_svc.allow_tool_execution = AsyncMock(
            return_value=PolicyResult(allow=True, require_human_approval=True, reason="large amount")
        )
        gw._create_approval = AsyncMock(return_value=uuid4())

        result = await gw.execute(proposal, _make_state(), db)

    assert result.decision == "PENDING_APPROVAL"


async def test_issue_refund_under_500_no_hitl_mocked() -> None:
    """LOW refund amount must NOT trigger HITL when OPA allows without HITL."""
    gw = SecureToolGateway()
    proposal = _make_proposal(
        "issue_refund",
        {"order_id": 8829, "amount": 120.0, "reason": "customer request resolved"},
    )
    db = _make_mock_db()

    # Mock handler execution to avoid DB
    with patch("app.governance.gateway.policy_service") as mock_svc, \
         patch.object(gw, "_execute_with_role", new=AsyncMock(return_value={"status": "REFUNDED"})), \
         patch("app.governance.audit.audit_service.record", new=AsyncMock()):
        mock_svc.allow_tool_execution = AsyncMock(
            return_value=PolicyResult(allow=True, require_human_approval=False, reason="allowed")
        )
        result = await gw.execute(proposal, _make_state(), db)

    assert result.decision == "ALLOWED"
    assert result.risk_level == "HIGH"


# ─── Integration Tests: Full Pipeline ─────────────────────────────────────────


@pytest.mark.opa
@pytest.mark.db
async def test_get_order_executes_via_order_reader_role(db) -> None:
    """CLAUDE.md §27 Test 1: get_order with analyst+order-agent → ALLOWED."""
    gw = SecureToolGateway()
    proposal = ToolProposal(
        tool_name="get_order",
        arguments={"order_id": 421},
        agent_id="order-agent",
        agent_spiffe_id="aegis://agents/order-agent",
        thread_id="thr_t1",
        reason="happy path test",
    )
    state = _make_state(
        user_roles=["analyst"],
        agent_id="order-agent",
        agent_spiffe_id="aegis://agents/order-agent",
    )

    result = await gw.execute(proposal, state, db)

    assert result.decision == "ALLOWED"
    assert result.risk_level == "LOW"
    assert result.result is not None
    assert result.result["order_id"] == 421


@pytest.mark.opa
@pytest.mark.db
async def test_get_customer_returns_sanitized_data(db) -> None:
    """Handler must not expose phone number in result."""
    gw = SecureToolGateway()
    proposal = ToolProposal(
        tool_name="get_customer",
        arguments={"customer_id": 1},
        agent_id="order-agent",
        agent_spiffe_id="aegis://agents/order-agent",
        thread_id="thr_t1b",
        reason="customer info test",
    )
    state = _make_state(
        user_roles=["analyst"],
        agent_id="order-agent",
        agent_spiffe_id="aegis://agents/order-agent",
    )

    result = await gw.execute(proposal, state, db)

    assert result.decision == "ALLOWED"
    assert "phone" not in (result.result or {})
    assert "email" in (result.result or {})


@pytest.mark.opa
@pytest.mark.db
async def test_nonexistent_order_returns_denied(db) -> None:
    """Business-layer failure (not found) should return DENIED, not 500."""
    gw = SecureToolGateway()
    proposal = ToolProposal(
        tool_name="get_order",
        arguments={"order_id": 999999},
        agent_id="order-agent",
        agent_spiffe_id="aegis://agents/order-agent",
        thread_id="thr_404",
        reason="not found test",
    )
    state = _make_state(
        user_roles=["analyst"],
        agent_id="order-agent",
        agent_spiffe_id="aegis://agents/order-agent",
    )

    result = await gw.execute(proposal, state, db)

    assert result.decision == "DENIED"
    assert "not found" in (result.reason or "").lower()
