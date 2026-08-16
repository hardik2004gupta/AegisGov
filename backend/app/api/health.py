"""
Health Check API — CLAUDE.md §19, Phase 4

GET /health — returns service health with dependency status.

Critical dependencies: PostgreSQL, OPA
Optional dependencies: Keycloak (identity), Langfuse (observability)

Returns 200 in all cases (even when degraded) so load balancers can always
reach this endpoint. Callers check the status field to determine actual health.
"""

from __future__ import annotations

import logging
import time

import httpx
from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


async def _check_postgres() -> dict:
    try:
        from app.db.session import AsyncSessionLocal
        t = time.monotonic()
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "healthy", "latency_ms": round((time.monotonic() - t) * 1000, 2)}
    except Exception as exc:
        logger.warning("PostgreSQL health check failed: %s", exc)
        return {"status": "unavailable"}


async def _check_opa() -> dict:
    try:
        t = time.monotonic()
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.opa_url}/health")
        latency = round((time.monotonic() - t) * 1000, 2)
        if resp.status_code == 200:
            return {"status": "healthy", "latency_ms": latency}
        return {"status": "unavailable", "http_status": resp.status_code}
    except Exception as exc:
        logger.warning("OPA health check failed: %s", exc)
        return {"status": "unavailable"}


async def _check_keycloak() -> dict:
    try:
        t = time.monotonic()
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(settings.keycloak_jwks_url)
        latency = round((time.monotonic() - t) * 1000, 2)
        if resp.status_code == 200:
            return {"status": "healthy", "latency_ms": latency}
        return {"status": "unavailable", "http_status": resp.status_code}
    except Exception as exc:
        logger.warning("Keycloak health check failed: %s", exc)
        return {"status": "unavailable"}


async def _check_langfuse() -> dict:
    from app.observability.tracer import is_enabled
    if not is_enabled():
        return {"status": "unconfigured"}
    try:
        t = time.monotonic()
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.langfuse_host}/api/public/health")
        latency = round((time.monotonic() - t) * 1000, 2)
        if resp.status_code == 200:
            return {"status": "healthy", "latency_ms": latency}
        return {"status": "unavailable", "http_status": resp.status_code}
    except Exception as exc:
        logger.warning("Langfuse health check failed: %s", exc)
        return {"status": "unavailable"}


@router.get("/health")
async def health() -> dict:
    """Check all service dependencies and return aggregate health status.

    Critical (postgres, opa): degraded if either is unavailable.
    Optional (keycloak, langfuse): informational only.
    """
    pg = await _check_postgres()
    opa = await _check_opa()
    keycloak = await _check_keycloak()
    langfuse = await _check_langfuse()

    critical_ok = (
        pg["status"] == "healthy"
        and opa["status"] == "healthy"
    )

    return {
        "status": "healthy" if critical_ok else "degraded",
        "service": "aegisgov-api",
        "version": "0.1.0",
        "dependencies": {
            "postgres": pg,
            "opa": opa,
            "keycloak": keycloak,
            "langfuse": langfuse,
        },
    }
