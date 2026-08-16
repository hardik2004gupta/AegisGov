"""
Test configuration and fixtures for AegisGov backend tests.

Phase 2 additions:
  - Test RSA key pair (in-memory, generated once per session)
  - make_jwt() helper to create signed test tokens
  - auth_headers() helper for authenticated API requests
  - JWKS injection into the identity module

Phase 3 additions:
  - _opa_available / _db_available: socket-check service availability
  - requires_opa / requires_db: skipif marks for integration tests
  - db: async DB session fixture with rollback for test isolation
"""

from __future__ import annotations

import base64
import socket
import time
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


# ─── Service Availability Checks ─────────────────────────────────────────────


def _port_open(host: str, port: int) -> bool:
    """Return True if a TCP connection can be established."""
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def _opa_available() -> bool:
    return _port_open("localhost", 8181)


def _db_available() -> bool:
    """Check the configured DATABASE_URL port, falling back to common defaults."""
    import os, re
    db_url = os.environ.get("DATABASE_URL", "")
    m = re.search(r":(\d+)/", db_url)
    if m:
        configured_port = int(m.group(1))
        if _port_open("localhost", configured_port):
            return True
    # Fallback: try common dev ports
    return _port_open("localhost", 5434) or _port_open("localhost", 5433) or _port_open("localhost", 5432)


# Evaluated once at collection time
_OPA_UP: bool = _opa_available()
_DB_UP: bool = _db_available()

requires_opa = pytest.mark.skipif(not _OPA_UP, reason="OPA not running on localhost:8181")
requires_db = pytest.mark.skipif(not _DB_UP, reason="PostgreSQL not running on localhost:5432/5433")


def pytest_collection_modifyitems(items):
    """Auto-skip tests marked opa/db when the corresponding service is down."""
    for item in items:
        if "opa" in item.keywords and not _OPA_UP:
            item.add_marker(pytest.mark.skip(reason="OPA not running on localhost:8181"))
        if "db" in item.keywords and not _DB_UP:
            item.add_marker(pytest.mark.skip(reason="PostgreSQL not running on localhost:5432/5433"))


# ─── NullPool Engine Fixture ─────────────────────────────────────────────────
# On Windows, the ProactorEventLoop is closed between async tests, leaving
# stale connections in the default connection pool. NullPool avoids this by
# opening and closing a fresh connection for every use.


@pytest.fixture(scope="session", autouse=True)
def use_null_pool():
    """Replace the shared SQLAlchemy engine with a NullPool engine for tests.

    On Windows the ProactorEventLoop closes between async tests, leaving stale
    pool connections. NullPool avoids this by opening a fresh connection per use.

    We must also patch every module that did a module-level
    `from app.db.session import AsyncSessionLocal` — those have their own
    local references that point at the original pooled factory.
    """
    if not _DB_UP:
        yield
        return

    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    import sys
    import app.db.session as session_module
    from app.core.config import settings

    null_engine = create_async_engine(settings.database_url, poolclass=NullPool)
    null_maker = async_sessionmaker(null_engine, class_=AsyncSession, expire_on_commit=False)

    session_module.engine = null_engine
    session_module.AsyncSessionLocal = null_maker

    # Patch every already-imported module that cached the old factory reference
    _modules_to_patch = [
        "app.graph.workflow",
        "app.api.approvals",
        "tests.test_hitl",
    ]
    for mod_name in _modules_to_patch:
        mod = sys.modules.get(mod_name)
        if mod is not None and hasattr(mod, "AsyncSessionLocal"):
            mod.AsyncSessionLocal = null_maker

    yield
    # NullPool has no idle connections to clean up


# ─── DB Session Fixture ───────────────────────────────────────────────────────


@pytest.fixture
async def db():
    """Async database session for integration tests.

    Tests manage their own data isolation:
     - Read-only tests (get_order, get_customer): no cleanup needed.
     - Write tests: use unique high-numbered IDs (9900+) with explicit
       delete-before-insert setup so reruns are idempotent.

    The gateway's _execute_with_role calls async with session.begin()
    which starts its own transaction; we must not pre-begin here.
    """
    if not _DB_UP:
        pytest.skip("PostgreSQL not available")

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session

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
