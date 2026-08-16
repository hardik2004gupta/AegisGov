"""
Human Identity — Keycloak JWT Verification

CLAUDE.md §5 — Critical rule:
    Authorization MUST derive from verified JWT claims only.
    Role information in the request body is UNTRUSTED and ignored.

JWT claims extracted:
    sub                  — user ID
    preferred_username   — display name
    realm_access.roles   — role list (analyst | billing | admin)
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

http_bearer = HTTPBearer(auto_error=False)

# ─── JWKS Cache ───────────────────────────────────────────────────────────────
# Keycloak JWKS rarely changes; cache for 5 minutes.

_jwks_cache: list[dict[str, Any]] | None = None
_jwks_cache_time: float = 0.0
_JWKS_TTL: float = 300.0


class CredentialsError(Exception):
    """Raised when JWT verification fails for any reason."""


class AuthenticatedUser(BaseModel):
    """Verified human identity extracted from a Keycloak-issued JWT."""

    user_id: str
    username: str
    roles: list[str]
    claims: dict[str, Any]


# ─── JWKS helpers (injectable for testing) ────────────────────────────────────


async def _fetch_jwks(jwks_url: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(jwks_url)
        resp.raise_for_status()
        return resp.json().get("keys", [])


async def _get_jwks(jwks_url: str | None = None) -> list[dict[str, Any]]:
    global _jwks_cache, _jwks_cache_time
    url = jwks_url or settings.keycloak_jwks_url
    now = time.monotonic()
    if _jwks_cache is None or (now - _jwks_cache_time) > _JWKS_TTL:
        _jwks_cache = await _fetch_jwks(url)
        _jwks_cache_time = now
    return _jwks_cache


def _invalidate_jwks_cache() -> None:
    """Force JWKS cache expiry. Call in tests to isolate key injection."""
    global _jwks_cache, _jwks_cache_time
    _jwks_cache = None
    _jwks_cache_time = 0.0


def _set_test_jwks(keys: list[dict[str, Any]]) -> None:
    """Inject a test JWKS directly, bypassing network fetch. Tests only."""
    global _jwks_cache, _jwks_cache_time
    _jwks_cache = keys
    _jwks_cache_time = time.monotonic()  # won't expire during the test run


# ─── Token Verification ───────────────────────────────────────────────────────


async def verify_token(
    token: str,
    *,
    jwks_url: str | None = None,
) -> AuthenticatedUser:
    """Verify a Keycloak-issued JWT and return the authenticated user.

    Fail-closed: any verification failure raises CredentialsError.
    Never returns an AuthenticatedUser if verification cannot be completed.
    """
    try:
        keys = await _get_jwks(jwks_url)
        if not keys:
            raise CredentialsError("JWKS returned no keys")

        # Match key by kid header; fall back to first key if no kid.
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        matching_key: dict[str, Any] | None = None
        for k in keys:
            if kid and k.get("kid") == kid:
                matching_key = k
                break
        if matching_key is None:
            matching_key = keys[0]

        payload: dict[str, Any] = jwt.decode(
            token,
            matching_key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Keycloak realm tokens omit audience
        )

        user_id: str = payload.get("sub", "")
        if not user_id:
            raise CredentialsError("Token missing 'sub' claim")

        username: str = payload.get("preferred_username") or user_id
        roles: list[str] = payload.get("realm_access", {}).get("roles", [])

        return AuthenticatedUser(
            user_id=user_id,
            username=username,
            roles=roles,
            claims=payload,
        )

    except JWTError as exc:
        raise CredentialsError(f"JWT verification failed: {exc}") from exc
    except httpx.HTTPError as exc:
        raise CredentialsError(f"JWKS fetch failed: {exc}") from exc


# ─── FastAPI Dependency ───────────────────────────────────────────────────────


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> AuthenticatedUser:
    """FastAPI dependency — extracts and verifies the bearer token.

    INVARIANT 2 (CLAUDE.md §26): Authorization derives from this verified JWT
    only. Any value in the request body is ignored for identity decisions.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await verify_token(credentials.credentials)
    except CredentialsError as exc:
        logger.warning("JWT verification failed (not logging token): %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
