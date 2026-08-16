"""
Phase 4: Audit Service and Audit API Tests

Tests the central audit service (app.governance.audit) and the REST
endpoints exposed by app.api.audit.

Tests that write DB rows are marked @pytest.mark.db.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from tests.conftest import auth_headers


def _unique_trace() -> str:
    """Return a trace_id guaranteed unique for this test run."""
    return f"trc_test_{uuid.uuid4().hex[:16]}"


# ─── Audit Service Unit Tests ─────────────────────────────────────────────────


def test_safe_payload_strips_sensitive_keys() -> None:
    """safe_payload() must remove credential-like keys before persisting."""
    from app.governance.audit import safe_payload

    raw = {
        "tool": "get_order",
        "order_id": 421,
        "password": "SHOULD_NOT_APPEAR",
        "authorization": "Bearer should_be_stripped",
        "api_key": "secret_key_value",
        "jwt": "token_value",
        "database_url": "postgresql://...",
        "risk": "LOW",
    }
    cleaned = safe_payload(raw)

    assert "password" not in cleaned
    assert "authorization" not in cleaned
    assert "api_key" not in cleaned
    assert "jwt" not in cleaned
    assert "database_url" not in cleaned
    assert cleaned["tool"] == "get_order"
    assert cleaned["risk"] == "LOW"
    assert cleaned["order_id"] == 421


@pytest.mark.db
async def test_audit_service_writes_event(db) -> None:
    """audit_service.record() creates a persisted AuditEvent row."""
    from app.db.models import AuditEvent
    from app.governance.audit import Decision, EventType, audit_service

    trace_id = _unique_trace()

    await audit_service.record(
        db,
        trace_id=trace_id,
        user_id="usr_test",
        agent_id="order-agent",
        action_type=EventType.TOOL_EXECUTION_COMPLETED,
        decision=Decision.ALLOWED,
        reason="Unit test event",
        payload={"tool": "get_order", "risk": "LOW"},
    )

    result = await db.execute(select(AuditEvent).where(AuditEvent.trace_id == trace_id))
    events = result.scalars().all()

    assert len(events) == 1
    evt = events[0]
    assert evt.action_type == EventType.TOOL_EXECUTION_COMPLETED
    assert evt.decision == Decision.ALLOWED
    assert evt.user_id == "usr_test"
    assert evt.agent_id == "order-agent"
    assert evt.payload == {"tool": "get_order", "risk": "LOW"}
    assert evt.reason == "Unit test event"


@pytest.mark.db
async def test_audit_service_strips_sensitive_payload_on_write(db) -> None:
    """audit_service.record() applies safe_payload before persisting."""
    from app.db.models import AuditEvent
    from app.governance.audit import Decision, EventType, audit_service

    trace_id = _unique_trace()

    await audit_service.record(
        db,
        trace_id=trace_id,
        user_id="usr_test",
        agent_id="system",
        action_type=EventType.IDENTITY_VERIFIED,
        decision=Decision.ALLOWED,
        payload={"username": "alice", "password": "SHOULD_NOT_BE_STORED", "role": "admin"},
    )

    result = await db.execute(select(AuditEvent).where(AuditEvent.trace_id == trace_id))
    evt = result.scalar_one()

    assert "password" not in evt.payload
    assert evt.payload.get("username") == "alice"
    assert evt.payload.get("role") == "admin"


# ─── Audit API Tests ──────────────────────────────────────────────────────────


def test_audit_list_requires_auth(client: TestClient) -> None:
    resp = client.get("/api/v1/audit")
    assert resp.status_code == 401


def test_audit_timeline_requires_auth(client: TestClient) -> None:
    resp = client.get("/api/v1/audit/some_trace_id")
    assert resp.status_code == 401


@pytest.mark.db
async def test_audit_list_returns_events(client: TestClient, db) -> None:
    """GET /api/v1/audit returns a paginated list of audit events."""
    from app.governance.audit import Decision, EventType, audit_service

    trace_id = _unique_trace()
    await audit_service.record(
        db,
        trace_id=trace_id,
        user_id="usr_list_test",
        agent_id="order-agent",
        action_type=EventType.POLICY_ALLOWED,
        decision=Decision.ALLOWED,
        reason="API list test",
    )

    resp = client.get(
        "/api/v1/audit",
        params={"trace_id": trace_id},
        headers=auth_headers(),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert "items" in body
    assert "total" in body
    assert "limit" in body
    assert "offset" in body
    assert body["total"] >= 1
    assert any(e["trace_id"] == trace_id for e in body["items"])


@pytest.mark.db
async def test_audit_list_filter_by_decision(client: TestClient, db) -> None:
    """Filtering by decision returns only matching events."""
    from app.governance.audit import Decision, EventType, audit_service

    trace_id = _unique_trace()
    await audit_service.record(
        db,
        trace_id=trace_id,
        user_id="usr_filter_test",
        agent_id="admin-agent",
        action_type=EventType.POLICY_DENIED,
        decision=Decision.DENIED,
        reason="Filter decision test",
    )

    resp = client.get(
        "/api/v1/audit",
        params={"decision": "DENIED", "trace_id": trace_id},
        headers=auth_headers(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert all(e["decision"] == "DENIED" for e in body["items"])


@pytest.mark.db
async def test_audit_list_filter_by_action_type(client: TestClient, db) -> None:
    """Filtering by action_type returns only matching events."""
    from app.governance.audit import Decision, EventType, audit_service

    trace_id = _unique_trace()
    await audit_service.record(
        db,
        trace_id=trace_id,
        user_id="usr_at_test",
        agent_id="billing-agent",
        action_type=EventType.APPROVAL_CREATED,
        decision=Decision.PENDING,
        reason="Action type filter test",
    )

    resp = client.get(
        "/api/v1/audit",
        params={"action_type": "APPROVAL_CREATED", "trace_id": trace_id},
        headers=auth_headers(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert all(e["action_type"] == "APPROVAL_CREATED" for e in body["items"])


@pytest.mark.db
async def test_audit_trace_timeline(client: TestClient, db) -> None:
    """GET /api/v1/audit/{trace_id} returns ordered timeline with summary."""
    from app.governance.audit import Decision, EventType, audit_service

    trace_id = _unique_trace()
    for action_type, decision in [
        (EventType.IDENTITY_VERIFIED, Decision.ALLOWED),
        (EventType.AGENT_HANDOFF_ALLOWED, Decision.ALLOWED),
        (EventType.TOOL_EXECUTION_COMPLETED, Decision.ALLOWED),
    ]:
        await audit_service.record(
            db,
            trace_id=trace_id,
            user_id="usr_tl_test",
            agent_id="order-agent",
            action_type=action_type,
            decision=decision,
            reason="Timeline test",
        )

    resp = client.get(f"/api/v1/audit/{trace_id}", headers=auth_headers())
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["trace_id"] == trace_id
    assert "events" in body
    assert "summary" in body
    assert len(body["events"]) == 3
    assert body["summary"]["total_events"] == 3
    assert body["summary"]["final_decision"] == "ALLOWED"
    assert "ALLOWED" in body["summary"]["decisions"]


@pytest.mark.db
def test_audit_list_pagination_params_reflected(client: TestClient) -> None:
    """Pagination params limit and offset are reflected in the response."""
    resp = client.get(
        "/api/v1/audit",
        params={"limit": 10, "offset": 5},
        headers=auth_headers(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["limit"] == 10
    assert body["offset"] == 5
