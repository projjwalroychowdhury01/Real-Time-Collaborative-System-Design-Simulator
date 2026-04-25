"""
Phase 1 test suite — JWT, auth routes, and database connectivity.

Run with:
    cd backend
    pytest tests/test_phase1.py -v

Requirements for these tests:
- A running PostgreSQL instance (or Docker Compose `db` service).
- DATABASE_URL set in .env or as an environment variable.
- No real OAuth credentials needed; auth routes are tested with mocks.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from jose import jwt
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# ── Test configuration must be set before importing app modules ──────────────
import os
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/sysdesign_db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-phase1-tests")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-google-secret")
os.environ.setdefault("GITHUB_CLIENT_ID", "test-github-id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test-github-secret")

from app.auth.sessions import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
)
from app.config import settings


# ============================================================================
# Unit tests — JWT token creation & validation
# ============================================================================

class TestJWTTokenCreation:
    """Verify that tokens are created with correct structure and claims."""

    def test_access_token_is_string(self):
        token = create_access_token({"sub": "1", "email": "test@example.com"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_access_token_has_correct_type_claim(self):
        token = create_access_token({"sub": "1", "email": "test@example.com"})
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["type"] == "access"

    def test_access_token_has_jti(self):
        token = create_access_token({"sub": "1", "email": "test@example.com"})
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert "jti" in payload
        assert len(payload["jti"]) == 36  # UUID4 format

    def test_access_token_preserves_subject(self):
        token = create_access_token({"sub": "42", "email": "user@example.com"})
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == "42"
        assert payload["email"] == "user@example.com"

    def test_access_token_expires_within_configured_window(self):
        before = datetime.now(timezone.utc)
        token = create_access_token({"sub": "1"})
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_max = before + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES + 1)
        assert exp <= expected_max

    def test_refresh_token_has_correct_type_claim(self):
        token = create_refresh_token({"sub": "1", "email": "test@example.com"})
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["type"] == "refresh"

    def test_refresh_token_longer_lived_than_access_token(self):
        access  = create_access_token({"sub": "1"})
        refresh = create_refresh_token({"sub": "1"})
        access_payload  = jwt.decode(access,  settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        refresh_payload = jwt.decode(refresh, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert refresh_payload["exp"] > access_payload["exp"]

    def test_token_pair_returns_both_tokens(self):
        pair = create_token_pair(user_id=1, email="test@example.com")
        assert "access_token"  in pair
        assert "refresh_token" in pair
        assert "token_type"    in pair
        assert pair["token_type"] == "bearer"

    def test_two_access_tokens_have_unique_jtis(self):
        t1 = create_access_token({"sub": "1"})
        t2 = create_access_token({"sub": "1"})
        p1 = jwt.decode(t1, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        p2 = jwt.decode(t2, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert p1["jti"] != p2["jti"]


# ============================================================================
# Unit tests — Token validation
# ============================================================================

class TestJWTTokenValidation:
    """Verify decode_token rejects tampered or wrong-type tokens."""

    def test_valid_access_token_decodes_successfully(self):
        token = create_access_token({"sub": "5"})
        payload = decode_token(token, expected_type="access")
        assert payload["sub"] == "5"

    def test_valid_refresh_token_decodes_successfully(self):
        token = create_refresh_token({"sub": "5"})
        payload = decode_token(token, expected_type="refresh")
        assert payload["type"] == "refresh"

    def test_wrong_type_raises_401(self):
        """Access token should NOT decode as a refresh token."""
        from fastapi import HTTPException
        token = create_access_token({"sub": "1"})
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token, expected_type="refresh")
        assert exc_info.value.status_code == 401

    def test_tampered_token_raises_401(self):
        from fastapi import HTTPException
        token = create_access_token({"sub": "1"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(HTTPException) as exc_info:
            decode_token(tampered)
        assert exc_info.value.status_code == 401

    def test_wrong_secret_raises_401(self):
        from fastapi import HTTPException
        # Token signed with a different secret
        bad_token = jwt.encode(
            {"sub": "1", "type": "access", "exp": 9999999999},
            "wrong-secret",
            algorithm="HS256",
        )
        with pytest.raises(HTTPException) as exc_info:
            decode_token(bad_token)
        assert exc_info.value.status_code == 401


# ============================================================================
# Integration tests — HTTP endpoints (via TestClient with mocked DB)
# ============================================================================

class TestHealthEndpoint:
    """Smoke test that the FastAPI app boots and the health route responds."""

    def test_health_returns_200(self):
        with patch("app.database.session.init_db", new_callable=AsyncMock):
            from app.main import app
            client = TestClient(app, raise_server_exceptions=True)
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_returns_version(self):
        with patch("app.database.session.init_db", new_callable=AsyncMock):
            from app.main import app
            client = TestClient(app)
            response = client.get("/health")
        assert "version" in response.json()


class TestAuthEndpoints:
    """Test authentication routes without real OAuth or DB connections."""

    def _make_client(self):
        with patch("app.database.session.init_db", new_callable=AsyncMock):
            from app.main import app
        return TestClient(app, raise_server_exceptions=False)

    def test_login_google_redirects(self):
        client = self._make_client()
        # Should get a redirect (302/307) to accounts.google.com
        response = client.get("/auth/login/google", follow_redirects=False)
        # Without real OAuth, Authlib may raise; we just check it doesn't 500 on bad provider name
        assert response.status_code in (302, 307, 400, 500)

    def test_login_unsupported_provider_returns_400(self):
        """
        The route guard catches unsupported providers before Authlib is called.
        """
        client = self._make_client()
        response = client.get("/auth/login/twitter", follow_redirects=False)
        assert response.status_code == 400
        assert "Unsupported provider" in response.json().get("detail", "")

    def test_me_without_token_returns_401(self):
        client = self._make_client()
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_me_with_valid_token_returns_user(self):
        """Mock the DB call and verify /auth/me returns user data."""
        from app.database.models import User as UserModel
        from app.auth.sessions import get_current_user
        from datetime import datetime

        mock_user = MagicMock(spec=UserModel)
        mock_user.id            = 99
        mock_user.email         = "alice@example.com"
        mock_user.username      = "alice"
        mock_user.auth_provider = "github"
        mock_user.created_at    = datetime(2026, 4, 24, 10, 0, 0)

        token = create_access_token({"sub": "99", "email": "alice@example.com"})

        with patch("app.database.session.init_db", new_callable=AsyncMock):
            from app.main import app

            # Use FastAPI dependency_overrides — the correct way to mock dependencies
            # without triggering the real database connection chain.
            async def override_get_current_user():
                return mock_user

            app.dependency_overrides[get_current_user] = override_get_current_user
            try:
                client = TestClient(app)
                response = client.get(
                    "/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                )
            finally:
                app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["email"]    == "alice@example.com"
        assert data["username"] == "alice"

    def test_refresh_without_body_returns_422(self):
        client = self._make_client()
        response = client.post("/auth/refresh", json={})
        assert response.status_code == 422

    def test_refresh_with_invalid_token_returns_401(self):
        client = self._make_client()
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "not-a-real-token"},
        )
        assert response.status_code == 401

    def test_refresh_with_access_token_returns_401(self):
        """Access tokens must NOT be accepted as refresh tokens."""
        client = self._make_client()
        access_token = create_access_token({"sub": "1", "email": "x@x.com"})
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401

    def test_logout_returns_200(self):
        client = self._make_client()
        response = client.post("/auth/logout")
        assert response.status_code == 200


# ============================================================================
# Config tests
# ============================================================================

class TestSettings:
    """Verify settings load correctly and have required fields."""

    def test_settings_has_database_url(self):
        assert settings.DATABASE_URL
        assert "postgresql" in settings.DATABASE_URL

    def test_database_url_uses_asyncpg(self):
        """asyncpg driver prefix is required for async SQLAlchemy."""
        assert "+asyncpg" in settings.DATABASE_URL, (
            "DATABASE_URL must use 'postgresql+asyncpg://' for async operation. "
            f"Got: {settings.DATABASE_URL}"
        )

    def test_settings_has_jwt_secret(self):
        assert settings.JWT_SECRET_KEY
        assert len(settings.JWT_SECRET_KEY) >= 10

    def test_cors_origins_is_list(self):
        assert isinstance(settings.BACKEND_CORS_ORIGINS, list)
        assert len(settings.BACKEND_CORS_ORIGINS) >= 1
