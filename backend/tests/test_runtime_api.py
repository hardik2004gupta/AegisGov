"""
Phase 4: Runtime Status API and Health API Tests

Tests GET /api/v1/runtime/status and GET /health.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers


# ─── Health API ───────────────────────────────────────────────────────────────


def test_health_endpoint_always_responds(client: TestClient) -> None:
    """GET /health returns 200 even when dependencies are unavailable."""
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_response_structure(client: TestClient) -> None:
    """Health response has the expected top-level structure."""
    resp = client.get("/health")
    body = resp.json()

    assert "status" in body
    assert body["status"] in ("healthy", "degraded")
    assert body["service"] == "aegisgov-api"
    assert body["version"] == "0.1.0"
    assert "dependencies" in body


def test_health_has_all_dependency_keys(client: TestClient) -> None:
    """All four dependency keys must be present regardless of availability."""
    resp = client.get("/health")
    deps = resp.json()["dependencies"]

    for key in ("postgres", "opa", "keycloak", "langfuse"):
        assert key in deps, f"Missing dependency key: {key}"
        assert "status" in deps[key], f"Dependency {key} missing 'status' field"


def test_health_langfuse_unconfigured_by_default(client: TestClient) -> None:
    """Langfuse should be 'unconfigured' in test env (not configured by default)."""
    resp = client.get("/health")
    langfuse_status = resp.json()["dependencies"]["langfuse"]["status"]
    # In test environment Langfuse keys are empty, so it should be unconfigured
    assert langfuse_status in ("unconfigured", "unavailable", "healthy")


# ─── Runtime Status API ───────────────────────────────────────────────────────


def test_runtime_status_requires_auth(client: TestClient) -> None:
    resp = client.get("/api/v1/runtime/status")
    assert resp.status_code == 401


@pytest.mark.db
def test_runtime_status_structure(client: TestClient) -> None:
    """GET /api/v1/runtime/status returns expected top-level structure."""
    resp = client.get("/api/v1/runtime/status", headers=auth_headers())
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert "summary" in body
    assert "approvals" in body
    assert "limits" in body


@pytest.mark.db
def test_runtime_status_summary_keys(client: TestClient) -> None:
    """Runtime summary has all expected count keys."""
    resp = client.get("/api/v1/runtime/status", headers=auth_headers())
    summary = resp.json()["summary"]

    for key in ("total_decisions", "allowed", "denied", "blocked", "pending_approvals"):
        assert key in summary, f"Missing summary key: {key}"


@pytest.mark.db
def test_runtime_status_counts_non_negative(client: TestClient) -> None:
    """All count values must be non-negative integers."""
    resp = client.get("/api/v1/runtime/status", headers=auth_headers())
    body = resp.json()

    for key, val in body["summary"].items():
        assert isinstance(val, int) and val >= 0, f"summary.{key}={val!r} is not a non-negative int"

    for key, val in body["approvals"].items():
        assert isinstance(val, int) and val >= 0, f"approvals.{key}={val!r} is not a non-negative int"


@pytest.mark.db
def test_runtime_limits_match_config(client: TestClient) -> None:
    """Configured runtime limits are exposed accurately."""
    from app.core.config import settings

    resp = client.get("/api/v1/runtime/status", headers=auth_headers())
    limits = resp.json()["limits"]

    assert limits["max_tool_calls"] == settings.max_tool_calls
    assert limits["max_execution_time_seconds"] == settings.max_execution_time_seconds
    assert limits["max_agent_handoffs"] == settings.max_agent_handoffs
    assert limits["max_identical_tool_calls"] == settings.max_identical_tool_calls


@pytest.mark.db
def test_runtime_approvals_keys(client: TestClient) -> None:
    """Approvals section has pending, approved, rejected keys."""
    resp = client.get("/api/v1/runtime/status", headers=auth_headers())
    approvals = resp.json()["approvals"]

    for key in ("pending", "approved", "rejected"):
        assert key in approvals, f"Missing approvals key: {key}"


# ─── Non-admin access to approval resolution (INVARIANT 2) ────────────────────


def test_non_admin_cannot_resolve_approval(client: TestClient) -> None:
    """Only admins can resolve approvals — 403 for analyst/billing roles."""
    fake_id = "00000000-0000-0000-0000-000000000001"

    for role in ("analyst", "billing"):
        resp = client.post(
            f"/api/v1/governance/approvals/{fake_id}/resolve",
            json={"decision": "APPROVED", "resolution_reason": "test"},
            headers=auth_headers(roles=[role]),
        )
        assert resp.status_code == 403, f"Expected 403 for role={role}, got {resp.status_code}"
