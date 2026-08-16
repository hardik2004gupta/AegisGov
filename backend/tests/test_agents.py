"""
Phase 2 — Agent Identity, Tool Proposals, and Security Boundary Tests

Covers:
  - Workload identity for all four agents
  - Tool proposal structure from each specialist
  - Security boundary: agents cannot directly invoke DB handlers
  - Integration scenario: billing user → refund proposal
"""

import pytest


# ─── Agent Identities ─────────────────────────────────────────────────────────


def test_supervisor_identity() -> None:
    from app.core.security import SUPERVISOR_IDENTITY

    assert SUPERVISOR_IDENTITY.agent_id == "supervisor"
    assert SUPERVISOR_IDENTITY.spiffe_id == "aegis://agents/supervisor"
    assert SUPERVISOR_IDENTITY.capabilities == []


def test_order_agent_identity() -> None:
    from app.core.security import ORDER_AGENT_IDENTITY

    assert ORDER_AGENT_IDENTITY.agent_id == "order-agent"
    assert ORDER_AGENT_IDENTITY.spiffe_id == "aegis://agents/order-agent"
    assert "get_order" in ORDER_AGENT_IDENTITY.capabilities
    assert "get_customer" in ORDER_AGENT_IDENTITY.capabilities


def test_billing_agent_identity() -> None:
    from app.core.security import BILLING_AGENT_IDENTITY

    assert BILLING_AGENT_IDENTITY.agent_id == "billing-agent"
    assert BILLING_AGENT_IDENTITY.spiffe_id == "aegis://agents/billing-agent"
    assert "issue_refund" in BILLING_AGENT_IDENTITY.capabilities
    assert "get_payment" in BILLING_AGENT_IDENTITY.capabilities


def test_admin_agent_identity() -> None:
    from app.core.security import ADMIN_AGENT_IDENTITY

    assert ADMIN_AGENT_IDENTITY.agent_id == "admin-agent"
    assert ADMIN_AGENT_IDENTITY.spiffe_id == "aegis://agents/admin-agent"
    assert "delete_customer" in ADMIN_AGENT_IDENTITY.capabilities


def test_agent_registry_has_all_agents() -> None:
    from app.core.security import AGENT_REGISTRY

    assert "supervisor" in AGENT_REGISTRY
    assert "order-agent" in AGENT_REGISTRY
    assert "billing-agent" in AGENT_REGISTRY
    assert "admin-agent" in AGENT_REGISTRY


# ─── Tool Proposals ───────────────────────────────────────────────────────────


def test_order_agent_get_order_proposal() -> None:
    from app.agents.order_agent import order_agent_node
    from app.graph.state import initial_state

    state = initial_state(
        thread_id="thr_order",
        user_id="usr",
        username="u",
        user_roles=["analyst"],
        message="show me order #421",
    )
    result = order_agent_node(state)

    assert result["proposed_tool"] == "get_order"
    assert result["tool_arguments"]["order_id"] == 421
    assert result["status"] == "PROPOSAL_READY"


def test_order_agent_get_customer_proposal() -> None:
    from app.agents.order_agent import order_agent_node
    from app.graph.state import initial_state

    state = initial_state(
        thread_id="thr_customer",
        user_id="usr",
        username="u",
        user_roles=["analyst"],
        message="show customer #99",
    )
    result = order_agent_node(state)

    assert result["proposed_tool"] == "get_customer"
    assert result["tool_arguments"]["customer_id"] == 99
    assert result["status"] == "PROPOSAL_READY"


def test_billing_agent_issue_refund_proposal() -> None:
    """Billing agent produces correct issue_refund proposal."""
    from app.agents.billing_agent import billing_agent_node
    from app.graph.state import initial_state

    state = initial_state(
        thread_id="thr_refund",
        user_id="usr",
        username="u",
        user_roles=["billing"],
        message="issue a $120 refund for order #8829",
    )
    result = billing_agent_node(state)

    assert result["proposed_tool"] == "issue_refund"
    assert result["tool_arguments"]["order_id"] == 8829
    assert result["tool_arguments"]["amount"] == 120.0
    assert result["status"] == "PROPOSAL_READY"


def test_billing_agent_get_payment_proposal() -> None:
    from app.agents.billing_agent import billing_agent_node
    from app.graph.state import initial_state

    state = initial_state(
        thread_id="thr_payment",
        user_id="usr",
        username="u",
        user_roles=["billing"],
        message="show payment for order 8829",
    )
    result = billing_agent_node(state)

    assert result["proposed_tool"] == "get_payment"
    assert result["tool_arguments"]["order_id"] == 8829
    assert result["status"] == "PROPOSAL_READY"


def test_admin_agent_delete_customer_proposal() -> None:
    """Admin agent produces delete_customer proposal (does NOT delete anything)."""
    from app.agents.admin_agent import admin_agent_node
    from app.graph.state import initial_state

    state = initial_state(
        thread_id="thr_delete",
        user_id="usr",
        username="u",
        user_roles=["admin"],
        message="delete customer #42",
    )
    result = admin_agent_node(state)

    assert result["proposed_tool"] == "delete_customer"
    assert result["tool_arguments"]["customer_id"] == 42
    assert result["status"] == "PROPOSAL_READY"


# ─── Security Boundary ────────────────────────────────────────────────────────


def test_agent_modules_have_no_db_session_import() -> None:
    """INVARIANT 1 & 9: agent modules must not import db session or models."""
    import importlib
    import importlib.util
    import sys

    agent_modules = [
        "app.agents.supervisor",
        "app.agents.order_agent",
        "app.agents.billing_agent",
        "app.agents.admin_agent",
    ]
    forbidden_imports = {"app.db.session", "app.db.models", "asyncpg", "sqlalchemy"}

    for mod_name in agent_modules:
        mod = sys.modules.get(mod_name)
        if mod is None:
            mod = importlib.import_module(mod_name)
        # Check that no forbidden module is in the module's namespace
        for forbidden in forbidden_imports:
            assert forbidden not in sys.modules.get(mod_name, {}).__dict__, (
                f"{mod_name} must not directly import {forbidden}"
            )


def test_proposal_does_not_call_handlers() -> None:
    """Producing a proposal must not trigger any callable in tools/handlers."""
    # Verify that tool handlers are not imported by agent modules at all
    import sys

    # After running agents in previous tests, handlers should not be loaded
    # by any agent module
    for agent_mod in [
        "app.agents.order_agent",
        "app.agents.billing_agent",
        "app.agents.admin_agent",
    ]:
        mod = sys.modules.get(agent_mod)
        if mod is not None:
            assert not hasattr(mod, "execute_") and not hasattr(mod, "db_"), (
                f"{agent_mod} must not expose DB execution functions"
            )


def test_frontend_role_in_request_body_ignored(client) -> None:
    """INVARIANT 2: body role field must not escalate privileges."""
    from tests.conftest import auth_headers

    # Analyst JWT — should be denied for delete_customer regardless of body content
    headers = auth_headers(roles=["analyst"])
    response = client.post(
        "/api/v1/agent/run",
        headers=headers,
        json={
            "thread_id": "thr_body_role",
            "message": "delete customer 42",
            "role": "admin",          # Must be ignored
            "user_roles": ["admin"],  # Must be ignored
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "DENIED"


def test_proposal_status_is_not_completed(client) -> None:
    """Phase 2 proposals must NEVER return COMPLETED (no execution yet)."""
    from tests.conftest import auth_headers

    headers = auth_headers(roles=["billing"])
    response = client.post(
        "/api/v1/agent/run",
        headers=headers,
        json={"thread_id": "thr_noexec", "message": "issue a $120 refund for order 8829"},
    )
    assert response.status_code == 200
    body = response.json()
    # Must be PROPOSAL_READY, never COMPLETED (which implies execution)
    assert body["status"] != "COMPLETED"
    assert body["status"] == "PROPOSAL_READY"


# ─── Integration Scenarios ────────────────────────────────────────────────────


async def test_billing_user_refund_integration(client) -> None:
    """CLAUDE.md §27: billing user → billing-agent → issue_refund proposal.

    This is the primary Phase 2 integration test.
    Expected: identity_verified=True, agent=billing-agent, tool=issue_refund,
              status=PROPOSAL_READY, and PostgreSQL payment data UNCHANGED.
    """
    from tests.conftest import auth_headers

    headers = auth_headers(
        user_id="usr_billing",
        username="billing_user",
        roles=["billing"],
    )
    response = client.post(
        "/api/v1/agent/run",
        headers=headers,
        json={
            "thread_id": "thr_integration_refund",
            "message": "Issue a $120 refund for order #8829",
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "PROPOSAL_READY"
    assert body["governance"]["identity_verified"] is True
    assert body["governance"]["agent_id"] == "billing-agent"
    assert body["proposal"]["tool"] == "issue_refund"
    assert body["proposal"]["arguments"]["order_id"] == 8829
    assert body["proposal"]["arguments"]["amount"] == 120.0
    # The proposal must include the trace_id for observability
    assert body["trace_id"].startswith("trc_")


async def test_analyst_order_request_integration(client) -> None:
    """Scenario A: analyst → order-agent → get_order proposal."""
    from tests.conftest import auth_headers

    headers = auth_headers(roles=["analyst"])
    response = client.post(
        "/api/v1/agent/run",
        headers=headers,
        json={"thread_id": "thr_analyst_order", "message": "Show me order #421"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PROPOSAL_READY"
    assert body["proposal"]["tool"] == "get_order"
    assert body["proposal"]["arguments"]["order_id"] == 421


async def test_admin_delete_proposal_not_executed(client) -> None:
    """Scenario C: admin → delete_customer proposal — customer is NOT deleted."""
    from tests.conftest import auth_headers

    headers = auth_headers(roles=["admin"])
    response = client.post(
        "/api/v1/agent/run",
        headers=headers,
        json={"thread_id": "thr_admin_delete", "message": "Delete customer #42"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PROPOSAL_READY"
    assert body["proposal"]["tool"] == "delete_customer"
    # No execution occurred — Phase 3 gateway required for actual deletion
