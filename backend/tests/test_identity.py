"""
Phase 1 Foundation Tests — API Health & Module Structure

Tests that actually execute in Phase 1:
  - GET /health returns healthy
  - SQLAlchemy models import without errors
  - Config loads from environment

Phase 2 tests (JWT verification, user extraction) are marked skip.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

# ─── Phase 1: Foundation ──────────────────────────────────────────────────────


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


# ─── Phase 2: Identity (not yet implemented) ──────────────────────────────────


@pytest.mark.skip(reason="Implemented in Phase 2")
def test_valid_jwt_returns_user_identity() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 2")
def test_expired_jwt_returns_401() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 2")
def test_missing_jwt_returns_401() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 2")
def test_frontend_role_claim_is_ignored() -> None:
    """Frontend-supplied role must not influence authorization (CLAUDE.md §3)."""
    pass


@pytest.mark.skip(reason="Implemented in Phase 2")
def test_analyst_role_extracted_from_jwt() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 2")
def test_billing_role_extracted_from_jwt() -> None:
    pass


@pytest.mark.skip(reason="Implemented in Phase 2")
def test_admin_role_extracted_from_jwt() -> None:
    pass
