"""
Phase 3: OPA Policy Tests

All tests here require:
  - Running OPA server (via Docker Compose)
  - aegis_policy.rego with Phase 3 rules loaded

Marked skip until Phase 3 implementation.
"""

import pytest


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_analyst_can_access_order_agent() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_analyst_cannot_access_admin_agent() -> None:
    """Privilege escalation must be denied (CLAUDE.md §27 Test 2)."""
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_billing_can_access_billing_agent() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_admin_can_access_all_agents() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_get_order_allowed_for_analyst() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_delete_customer_denied_for_analyst() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_opa_unavailable_returns_deny() -> None:
    """Fail-closed contract (CLAUDE.md §11)."""
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_unknown_tool_returns_deny() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_missing_identity_returns_deny() -> None:
    pass
