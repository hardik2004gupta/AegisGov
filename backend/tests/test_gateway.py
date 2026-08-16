"""
Phase 3: Secure Tool Gateway Tests

Tests the full gateway pipeline (CLAUDE.md §8):
  Agent Proposal → Registry → Pydantic → Runtime Limits → OPA →
  Risk → [HITL?] → Execute → Audit

Marked skip until Phase 3 implementation.
"""

import pytest


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_unregistered_tool_fails_closed() -> None:
    """INVARIANT 7: Unregistered tool must never execute (CLAUDE.md §26)."""
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_invalid_parameters_blocked_before_handler() -> None:
    """INVARIANT 6: Invalid parameters must not reach handlers (CLAUDE.md §26)."""
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_get_order_executes_via_order_reader_role() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_issue_refund_under_500_executes_automatically() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_issue_refund_over_500_triggers_hitl() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_delete_customer_always_triggers_hitl() -> None:
    """INVARIANT 5: CRITICAL action must never auto-execute (CLAUDE.md §26)."""
    pass


@pytest.mark.skip(reason="Implemented in Phase 3")
def test_gateway_pipeline_order_is_enforced() -> None:
    """Registry → Pydantic → Limits → OPA → Risk — order is invariant."""
    pass
