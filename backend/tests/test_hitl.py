"""
Phase 3: Human-in-the-Loop (HITL) Tests

Tests the approval workflow for CRITICAL and high-value operations.
CLAUDE.md §15 — approval state must be persisted and survive restarts.

Mandatory test scenario (CLAUDE.md §27 Test 4):
  admin → delete_customer(42) → CRITICAL risk → HITL pause →
  approval persisted → human approves → gateway executes → audit

INVARIANT 8: Rejected approval MUST NOT result in a database mutation.

All tests require both OPA and PostgreSQL (integration mark).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
from sqlalchemy import select, update

from app.core.security import ToolProposal
from app.db.models import ApprovalRequest, AuditEvent, Customer, Payment
from app.db.session import AsyncSessionLocal
from app.governance.gateway import SecureToolGateway
from app.graph.state import initial_state

pytestmark = [pytest.mark.opa, pytest.mark.db]


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _admin_state(**kwargs):
    s = initial_state(
        thread_id="thr_hitl",
        user_id="usr_admin_001",
        username="admin_user",
        user_roles=["admin"],
        message="admin request",
        trace_id="trc_hitl001",
    )
    s.update(
        agent_id="admin-agent",
        agent_spiffe_id="aegis://agents/admin-agent",
    )
    s.update(kwargs)
    return s


def _delete_proposal(customer_id: int) -> ToolProposal:
    return ToolProposal(
        tool_name="delete_customer",
        arguments={"customer_id": customer_id, "reason": "HITL integration test"},
        agent_id="admin-agent",
        agent_spiffe_id="aegis://agents/admin-agent",
        thread_id="thr_hitl",
        reason="test scenario",
    )


async def _ensure_test_customer(db, customer_id: int) -> None:
    """Insert a throwaway customer, deleting any existing record first."""
    from sqlalchemy import delete
    await db.execute(delete(Payment).where(Payment.customer_id == customer_id))
    await db.execute(delete(Customer).where(Customer.id == customer_id))
    await db.commit()
    c = Customer(id=customer_id, email=f"hitl_{customer_id}@test.internal", full_name="HITL Test")
    db.add(c)
    await db.commit()


async def _reset_payment(db, order_id: int) -> None:
    """Reset a payment back to COMPLETED status for idempotent test reruns."""
    await db.execute(
        update(Payment).where(Payment.order_id == order_id).values(
            status="COMPLETED",
            refund_amount=None,
            refund_reason=None,
            refunded_at=None,
        )
    )
    await db.commit()


# ─── Tests ────────────────────────────────────────────────────────────────────


async def test_delete_customer_creates_pending_approval(db) -> None:
    """INVARIANT 5: delete_customer must pause with PENDING_APPROVAL, never execute."""
    await _ensure_test_customer(db, customer_id=9998)
    gw = SecureToolGateway()

    result = await gw.execute(_delete_proposal(9998), _admin_state(), db)

    assert result.decision == "PENDING_APPROVAL"
    assert result.approval_id is not None
    assert result.risk_level == "CRITICAL"

    # Verify the approval request is in the DB
    approval_row = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == UUID(result.approval_id))
    )
    pending = approval_row.scalar_one_or_none()
    assert pending is not None
    assert pending.status == "PENDING"
    assert pending.tool_name == "delete_customer"

    # Customer must NOT have been deleted
    cust = await db.execute(select(Customer).where(Customer.id == 9998))
    assert cust.scalar_one_or_none() is not None


async def test_approved_action_executes_and_deletes_customer(db) -> None:
    """Approved delete_customer must execute and remove the customer record."""
    await _ensure_test_customer(db, customer_id=9997)
    gw = SecureToolGateway()

    # Trigger HITL pause
    pause_result = await gw.execute(_delete_proposal(9997), _admin_state(), db)
    assert pause_result.decision == "PENDING_APPROVAL"
    assert pause_result.approval_id is not None

    # Fetch the persisted approval
    approval_row = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == UUID(pause_result.approval_id))
    )
    approval = approval_row.scalar_one()

    # Mark as approved (simulates admin resolving via UI)
    approval.status = "APPROVED"
    approval.approved_by = "admin-test"
    approval.resolved_at = datetime.now(timezone.utc)
    await db.commit()

    # Execute the approved action
    exec_result = await gw.execute_approved_action(approval, db, approver_id="admin-test")

    assert exec_result["status"] == "DELETED"
    assert exec_result["customer_id"] == 9997

    # Customer must be gone
    cust = await db.execute(select(Customer).where(Customer.id == 9997))
    assert cust.scalar_one_or_none() is None


async def test_rejected_approval_prevents_database_mutation(db) -> None:
    """INVARIANT 8: Rejected approval must NOT result in DB mutation."""
    await _ensure_test_customer(db, customer_id=9996)
    gw = SecureToolGateway()

    pause_result = await gw.execute(_delete_proposal(9996), _admin_state(), db)
    assert pause_result.decision == "PENDING_APPROVAL"

    # Reject — don't call execute_approved_action
    approval_row = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == UUID(pause_result.approval_id))
    )
    approval = approval_row.scalar_one()
    approval.status = "REJECTED"
    approval.approved_by = "admin-test"
    approval.resolved_at = datetime.now(timezone.utc)
    await db.commit()

    # Customer must still exist (INVARIANT 8)
    cust = await db.execute(select(Customer).where(Customer.id == 9996))
    assert cust.scalar_one_or_none() is not None


async def test_approval_state_persisted_to_postgresql(db) -> None:
    """Approval state must survive server restarts (PostgreSQL-backed)."""
    await _ensure_test_customer(db, customer_id=9995)
    gw = SecureToolGateway()

    result = await gw.execute(_delete_proposal(9995), _admin_state(), db)
    assert result.approval_id is not None

    # Simulate "restart" — open a brand-new session and re-fetch
    async with AsyncSessionLocal() as fresh:
        row = await fresh.execute(
            select(ApprovalRequest).where(ApprovalRequest.id == UUID(result.approval_id))
        )
        persisted = row.scalar_one_or_none()

    assert persisted is not None
    assert persisted.status == "PENDING"
    assert persisted.tool_name == "delete_customer"


async def test_high_value_refund_triggers_hitl(db) -> None:
    """issue_refund with amount > $500 must trigger HITL (CLAUDE.md §14)."""
    gw = SecureToolGateway()
    proposal = ToolProposal(
        tool_name="issue_refund",
        arguments={"order_id": 8829, "amount": 700.0, "reason": "large refund integration test"},
        agent_id="billing-agent",
        agent_spiffe_id="aegis://agents/billing-agent",
        thread_id="thr_hitl_refund",
        reason="test",
    )
    state = initial_state(
        thread_id="thr_hitl_refund",
        user_id="usr_billing_001",
        username="billing_user",
        user_roles=["billing"],
        message="test",
    )
    state.update(agent_id="billing-agent", agent_spiffe_id="aegis://agents/billing-agent")

    result = await gw.execute(proposal, state, db)

    assert result.decision == "PENDING_APPROVAL"
    assert result.risk_level == "HIGH"


async def test_low_value_refund_executes_automatically(db) -> None:
    """issue_refund with amount <= $500 must auto-execute without HITL."""
    # Reset payment for order 9002 to COMPLETED in case prior test left it refunded
    await _reset_payment(db, order_id=9002)

    gw = SecureToolGateway()
    proposal = ToolProposal(
        tool_name="issue_refund",
        arguments={"order_id": 9002, "amount": 75.0, "reason": "low value auto-refund test"},
        agent_id="billing-agent",
        agent_spiffe_id="aegis://agents/billing-agent",
        thread_id="thr_low_refund",
        reason="test",
    )
    state = initial_state(
        thread_id="thr_low_refund",
        user_id="usr_billing_001",
        username="billing_user",
        user_roles=["billing"],
        message="test",
    )
    state.update(agent_id="billing-agent", agent_spiffe_id="aegis://agents/billing-agent")

    result = await gw.execute(proposal, state, db)

    assert result.decision == "ALLOWED"
    assert result.risk_level == "HIGH"
    assert result.result is not None
    assert result.result["status"] == "REFUNDED"


async def test_audit_event_written_for_hitl_action(db) -> None:
    """Every HITL pause must generate a persisted audit event."""
    await _ensure_test_customer(db, customer_id=9994)
    gw = SecureToolGateway()

    trace = "trc_audit_hitl_test"
    result = await gw.execute(_delete_proposal(9994), _admin_state(trace_id=trace), db)
    assert result.decision == "PENDING_APPROVAL"

    # Verify audit event in a fresh session
    async with AsyncSessionLocal() as fresh:
        events_result = await fresh.execute(
            select(AuditEvent).where(AuditEvent.trace_id == trace)
        )
        audit_rows = events_result.scalars().all()

    assert len(audit_rows) >= 1
    decisions = {e.decision for e in audit_rows}
    assert "PENDING" in decisions
