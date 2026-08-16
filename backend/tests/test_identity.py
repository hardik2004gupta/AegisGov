"""
Phase 2 — Identity Tests

Verifies Keycloak JWT verification and human identity extraction.

CLAUDE.md §5 — Critical rule:
    Authorization MUST derive from verified JWT claims only.
    Role information in the request body is UNTRUSTED and ignored.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

# ─── Phase 1: Foundation (preserved) ─────────────────────────────────────────


def test_health_endpoint_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_returns_correct_body(client: TestClient) -> None:
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "aegisgov-api"
    assert "version" in body


def test_openapi_schema_available_in_dev() -> None:
    with TestClient(app) as c:
        response = c.get("/docs")
        assert response.status_code == 200


def test_models_import() -> None:
    from app.db.models import (  # noqa: F401
        ApprovalRequest,
        AuditEvent,
        Customer,
        Order,
        Payment,
    )


def test_config_loads() -> None:
    from app.core.config import settings

    assert settings.max_tool_calls == 8
    assert settings.max_execution_time_seconds == 60
    assert settings.max_agent_handoffs == 4
    assert settings.max_identical_tool_calls == 3


# ─── Phase 2: JWT Verification ───────────────────────────────────────────────


async def test_missing_jwt_returns_401(client: TestClient) -> None:
    """No Authorization header → 401."""
    response = client.post(
        "/api/v1/agent/run",
        json={"thread_id": "thr_001", "message": "show order 421"},
    )
    assert response.status_code == 401


async def test_malformed_jwt_returns_401(client: TestClient) -> None:
    """Non-JWT bearer token → 401."""
    response = client.post(
        "/api/v1/agent/run",
        headers={"Authorization": "Bearer not.a.real.jwt"},
        json={"thread_id": "thr_001", "message": "show order 421"},
    )
    assert response.status_code == 401


async def test_invalid_signature_returns_401(client: TestClient) -> None:
    """JWT signed with a different key → 401."""
    from tests.conftest import auth_headers

    headers = auth_headers(wrong_key=True)
    response = client.post(
        "/api/v1/agent/run",
        headers=headers,
        json={"thread_id": "thr_001", "message": "show order 421"},
    )
    assert response.status_code == 401


async def test_expired_jwt_returns_401(client: TestClient) -> None:
    """Expired JWT → 401."""
    from tests.conftest import auth_headers

    headers = auth_headers(expired=True)
    response = client.post(
        "/api/v1/agent/run",
        headers=headers,
        json={"thread_id": "thr_001", "message": "show order 421"},
    )
    assert response.status_code == 401


async def test_valid_analyst_jwt_authenticated() -> None:
    """Valid analyst JWT extracts correct identity."""
    from tests.conftest import make_jwt
    from app.core.identity import verify_token

    token = make_jwt(user_id="usr_analyst", username="analyst_user", roles=["analyst"])
    user = await verify_token(token)

    assert user.user_id == "usr_analyst"
    assert user.username == "analyst_user"
    assert "analyst" in user.roles


async def test_valid_billing_jwt_authenticated() -> None:
    """Valid billing JWT extracts correct identity."""
    from tests.conftest import make_jwt
    from app.core.identity import verify_token

    token = make_jwt(user_id="usr_billing", username="billing_user", roles=["billing"])
    user = await verify_token(token)

    assert user.user_id == "usr_billing"
    assert "billing" in user.roles


async def test_valid_admin_jwt_authenticated() -> None:
    """Valid admin JWT extracts correct identity."""
    from tests.conftest import make_jwt
    from app.core.identity import verify_token

    token = make_jwt(user_id="usr_admin", username="admin_user", roles=["admin"])
    user = await verify_token(token)

    assert user.user_id == "usr_admin"
    assert "admin" in user.roles


async def test_roles_come_from_verified_jwt() -> None:
    """Roles are extracted from JWT realm_access.roles, not from request body."""
    from tests.conftest import make_jwt
    from app.core.identity import verify_token

    token = make_jwt(roles=["billing"])
    user = await verify_token(token)

    # Roles must come from the JWT
    assert "billing" in user.roles
    assert "admin" not in user.roles


async def test_frontend_role_claim_is_ignored(client: TestClient) -> None:
    """INVARIANT 2: body-supplied role is ignored; JWT role governs.

    An analyst JWT with a body claiming 'admin' role must be denied
    when attempting an admin-only operation, because the backend uses
    only the verified JWT role ('analyst').
    """
    from tests.conftest import auth_headers

    # analyst JWT but body contains a fake role field (not processed)
    headers = auth_headers(roles=["analyst"])
    response = client.post(
        "/api/v1/agent/run",
        headers=headers,
        json={
            "thread_id": "thr_002",
            "message": "delete customer #42",
            # Providing a role in the body — must be ignored
            "role": "admin",
        },
    )
    # Request should be processed; analyst cannot reach admin-agent
    assert response.status_code == 200
    body = response.json()
    # Handoff to admin-agent must be denied because JWT says analyst
    assert body["status"] == "DENIED"
