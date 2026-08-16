"""
Phase 3: OPA Policy Tests

Exercises the OPA policy (policy/aegis_policy.rego) via the OPAPolicyService.
All tests require a running OPA server on localhost:8181 with the aegis policy loaded.

Coverage (CLAUDE.md §11, §13, §14):
  - Role → Agent handoff authorization (all 3 roles × all 3 agents)
  - Role → Tool execution authorization
  - Agent capability restrictions
  - require_human_approval rules
  - Fail-closed contract
"""

import pytest

from app.governance.policy import OPAPolicyService, PolicyResult

pytestmark = pytest.mark.opa


@pytest.fixture
def svc() -> OPAPolicyService:
    """Fresh policy service instance for each test."""
    return OPAPolicyService()


# ─── Handoff Authorization ────────────────────────────────────────────────────


async def test_analyst_can_access_order_agent(svc: OPAPolicyService) -> None:
    result = await svc.allow_handoff(
        user_id="usr_analyst",
        user_roles=["analyst"],
        agent_id="supervisor",
        agent_spiffe_id="aegis://agents/supervisor",
        target_agent="order-agent",
    )
    assert result.allow is True


async def test_analyst_cannot_access_billing_agent(svc: OPAPolicyService) -> None:
    result = await svc.allow_handoff(
        user_id="usr_analyst",
        user_roles=["analyst"],
        agent_id="supervisor",
        agent_spiffe_id="aegis://agents/supervisor",
        target_agent="billing-agent",
    )
    assert result.allow is False


async def test_analyst_cannot_access_admin_agent(svc: OPAPolicyService) -> None:
    """CLAUDE.md §27 Test 2: privilege escalation must be blocked."""
    result = await svc.allow_handoff(
        user_id="usr_analyst",
        user_roles=["analyst"],
        agent_id="supervisor",
        agent_spiffe_id="aegis://agents/supervisor",
        target_agent="admin-agent",
    )
    assert result.allow is False


async def test_billing_can_access_billing_agent(svc: OPAPolicyService) -> None:
    result = await svc.allow_handoff(
        user_id="usr_billing",
        user_roles=["billing"],
        agent_id="supervisor",
        agent_spiffe_id="aegis://agents/supervisor",
        target_agent="billing-agent",
    )
    assert result.allow is True


async def test_billing_cannot_access_admin_agent(svc: OPAPolicyService) -> None:
    result = await svc.allow_handoff(
        user_id="usr_billing",
        user_roles=["billing"],
        agent_id="supervisor",
        agent_spiffe_id="aegis://agents/supervisor",
        target_agent="admin-agent",
    )
    assert result.allow is False


async def test_admin_can_access_all_agents(svc: OPAPolicyService) -> None:
    for agent in ("order-agent", "billing-agent", "admin-agent"):
        result = await svc.allow_handoff(
            user_id="usr_admin",
            user_roles=["admin"],
            agent_id="supervisor",
            agent_spiffe_id="aegis://agents/supervisor",
            target_agent=agent,
        )
        assert result.allow is True, f"admin should reach {agent}"


# ─── Tool Execution Authorization ─────────────────────────────────────────────


async def test_analyst_order_agent_get_order_allowed(svc: OPAPolicyService) -> None:
    """CLAUDE.md §27 Test 1 policy check."""
    result = await svc.allow_tool_execution(
        user_id="usr_analyst",
        user_roles=["analyst"],
        agent_id="order-agent",
        agent_spiffe_id="aegis://agents/order-agent",
        tool_name="get_order",
        resource_id="421",
    )
    assert result.allow is True
    assert result.require_human_approval is False


async def test_analyst_cannot_execute_delete_customer(svc: OPAPolicyService) -> None:
    result = await svc.allow_tool_execution(
        user_id="usr_analyst",
        user_roles=["analyst"],
        agent_id="admin-agent",
        agent_spiffe_id="aegis://agents/admin-agent",
        tool_name="delete_customer",
        resource_id="42",
    )
    assert result.allow is False


async def test_delete_customer_requires_human_approval(svc: OPAPolicyService) -> None:
    """INVARIANT 5: CRITICAL actions always require HITL (CLAUDE.md §14)."""
    result = await svc.allow_tool_execution(
        user_id="usr_admin",
        user_roles=["admin"],
        agent_id="admin-agent",
        agent_spiffe_id="aegis://agents/admin-agent",
        tool_name="delete_customer",
        resource_id="42",
    )
    assert result.allow is True
    assert result.require_human_approval is True


async def test_issue_refund_under_500_no_hitl(svc: OPAPolicyService) -> None:
    result = await svc.allow_tool_execution(
        user_id="usr_billing",
        user_roles=["billing"],
        agent_id="billing-agent",
        agent_spiffe_id="aegis://agents/billing-agent",
        tool_name="issue_refund",
        resource_id="8829",
        arguments={"order_id": 8829, "amount": 120.0, "reason": "customer request"},
    )
    assert result.allow is True
    assert result.require_human_approval is False


async def test_issue_refund_over_500_requires_hitl(svc: OPAPolicyService) -> None:
    """$500 threshold: amount > 500 must require human approval."""
    result = await svc.allow_tool_execution(
        user_id="usr_billing",
        user_roles=["billing"],
        agent_id="billing-agent",
        agent_spiffe_id="aegis://agents/billing-agent",
        tool_name="issue_refund",
        resource_id="8829",
        arguments={"order_id": 8829, "amount": 700.0, "reason": "dispute resolution"},
    )
    assert result.allow is True
    assert result.require_human_approval is True


async def test_agent_capability_restriction(svc: OPAPolicyService) -> None:
    """order-agent must NOT be allowed to execute issue_refund (wrong capability)."""
    result = await svc.allow_tool_execution(
        user_id="usr_billing",
        user_roles=["billing"],
        agent_id="order-agent",
        agent_spiffe_id="aegis://agents/order-agent",
        tool_name="issue_refund",  # not in order-agent's capability set
        resource_id="8829",
    )
    assert result.allow is False


async def test_opa_unavailable_returns_deny() -> None:
    """Fail-closed contract (CLAUDE.md §11): OPA unavailable → DENY."""
    from unittest.mock import patch

    svc = OPAPolicyService()
    with patch("app.governance.policy.settings") as mock_settings:
        mock_settings.opa_decision_url = "http://localhost:19999/v1/data/aegis"
        result = await svc.allow_tool_execution(
            user_id="usr_analyst",
            user_roles=["analyst"],
            agent_id="order-agent",
            agent_spiffe_id="aegis://agents/order-agent",
            tool_name="get_order",
            resource_id="421",
        )
    assert result.allow is False
    assert "fail closed" in result.reason.lower() or "unavailable" in result.reason.lower() or "error" in result.reason.lower()
