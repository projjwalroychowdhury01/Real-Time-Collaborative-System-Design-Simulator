"""
Pytest shared fixtures for the backend test suite.

Improvement #8: Centralises app creation, DB patching, and Redis mocking into
session-scoped fixtures so individual test modules don't repeat boilerplate and
can't accidentally leave dependency_overrides dirty across test isolation
boundaries.

Usage in test modules
---------------------
    def test_something(client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_with_auth(auth_client):
        response = auth_client.get("/auth/me")
        assert response.status_code == 200
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


# ── Test environment guard ────────────────────────────────────────────────────
# Set env vars BEFORE any app module is imported so Settings validators pass.
import os
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/sysdesign_db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-phase1-tests-0000")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-google-secret")
os.environ.setdefault("GITHUB_CLIENT_ID", "test-github-id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test-github-secret")


# ── Redis mock (session-scoped so it's shared across all tests) ───────────────
@pytest.fixture(scope="session")
def mock_redis():
    """Provides a session-scoped async Redis mock.

    is_token_revoked → returns False (no tokens revoked in tests)
    revoke_token     → silently succeeds
    ping             → succeeds
    """
    mock = AsyncMock()
    mock.exists.return_value = 0   # not revoked
    mock.setex.return_value = True
    mock.ping.return_value = True
    mock.aclose.return_value = None
    return mock


# ── FastAPI app (session-scoped) ──────────────────────────────────────────────
@pytest.fixture(scope="session")
def app(mock_redis):
    """Create the FastAPI app once per test session with:
    - DB init patched out (no real PostgreSQL needed)
    - Redis patched out (no real Redis needed)
    """
    with patch("app.database.session.init_db", new_callable=AsyncMock), \
         patch("app.redis_client.get_redis", return_value=mock_redis), \
         patch("app.redis_client.close_redis", new_callable=AsyncMock):
        from app.main import app as _app
        yield _app


# ── TestClient (function-scoped for isolation) ────────────────────────────────
@pytest.fixture
def client(app):
    """Unauthenticated TestClient. Use for public endpoint tests."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def client_strict(app):
    """Like client but raises server exceptions (useful for debugging)."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ── Authenticated client ──────────────────────────────────────────────────────
@pytest.fixture
def mock_user():
    """A realistic mock User model instance."""
    from app.database.models import User as UserModel

    u = MagicMock(spec=UserModel)
    u.id            = 42
    u.email         = "alice@example.com"
    u.username      = "alice_ab12cd34"
    u.auth_provider = "github"
    u.created_at    = datetime(2026, 4, 24, 10, 0, 0)
    return u


@pytest.fixture
def auth_client(app, mock_user):
    """TestClient with dependency_overrides that inject a mock authenticated user.

    Cleans up overrides after the test so isolation is guaranteed.
    """
    from app.auth.sessions import get_current_user

    async def _override():
        return mock_user

    app.dependency_overrides[get_current_user] = _override
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)
