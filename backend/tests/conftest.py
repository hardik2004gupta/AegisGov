"""
Test configuration and fixtures for AegisGov backend tests.

Phase 2 additions:
  - Test RSA key pair (in-memory, generated once per session)
  - make_jwt() helper to create signed test tokens
  - auth_headers() helper for authenticated API requests
  - JWKS injection into the identity module
"""

from __future__ import annotations

import base64
import time
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app

# ─── Test RSA Key Pair ────────────────────────────────────────────────────────
# Generated once per session; never touches the network.

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)

_TEST_PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend(),
)
_TEST_PRIVATE_PEM: bytes = _TEST_PRIVATE_KEY.private_bytes(
    Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
)

_DIFFERENT_PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend(),
)
_DIFFERENT_PRIVATE_PEM: bytes = _DIFFERENT_PRIVATE_KEY.private_bytes(
    Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
)


def _int_to_base64url(n: int) -> str:
    length = (n.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(n.to_bytes(length, "big")).decode().rstrip("=")


def _make_jwk(key: rsa.RSAPrivateKey, kid: str = "test-key-001") -> dict:
    pub = key.public_key().public_numbers()
    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": kid,
        "n": _int_to_base64url(pub.n),
        "e": _int_to_base64url(pub.e),
    }


TEST_JWK: dict = _make_jwk(_TEST_PRIVATE_KEY, "test-key-001")
DIFFERENT_JWK: dict = _make_jwk(_DIFFERENT_PRIVATE_KEY, "other-key")


def make_jwt(
    user_id: str = "test-user-001",
    username: str = "test_user",
    roles: list[str] | None = None,
    *,
    expired: bool = False,
    wrong_key: bool = False,
    missing_sub: bool = False,
) -> str:
    """Create a signed test JWT. By default produces a valid analyst token."""
    from jose import jwt as jose_jwt

    now = int(time.time())
    exp = now - 60 if expired else now + 3600

    claims: dict = {
        "preferred_username": username,
        "realm_access": {"roles": roles if roles is not None else ["analyst"]},
        "iat": now,
        "exp": exp,
        "jti": "test-jti",
        "iss": "http://localhost:8080/realms/aegisgov",
    }
    if not missing_sub:
        claims["sub"] = user_id

    key = _DIFFERENT_PRIVATE_PEM if wrong_key else _TEST_PRIVATE_PEM
    kid = "other-key" if wrong_key else "test-key-001"

    return jose_jwt.encode(
        claims,
        key,
        algorithm="RS256",
        headers={"kid": kid},
    )


def auth_headers(
    user_id: str = "test-user-001",
    username: str = "test_user",
    roles: list[str] | None = None,
    **kwargs,
) -> dict[str, str]:
    """Return Authorization headers for use in TestClient requests."""
    token = make_jwt(user_id=user_id, username=username, roles=roles, **kwargs)
    return {"Authorization": f"Bearer {token}"}


# ─── JWKS injection fixture ───────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def inject_test_jwks() -> Generator[None, None, None]:
    """Inject test JWKS before each test and reset after.

    Prevents tests from reaching the Keycloak network.
    """
    from app.core import identity as id_module

    id_module._set_test_jwks([TEST_JWK])
    yield
    id_module._invalidate_jwks_cache()


# ─── TestClient ───────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
