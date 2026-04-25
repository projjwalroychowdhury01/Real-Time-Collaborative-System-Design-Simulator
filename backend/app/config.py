"""
Application configuration loaded from environment variables / .env file.

The DATABASE_URL must use the asyncpg driver scheme:
    postgresql+asyncpg://user:password@host:port/dbname

The .env file is loaded from the *backend/* working directory when running
`uvicorn app.main:app` directly, or from the root when using Docker Compose
via `env_file: .env`.
"""
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Known weak placeholder values that must not be used in production.
_WEAK_JWT_SECRETS = frozenset({
    "changeme-replace-with-a-long-random-secret",
    "change-me-to-a-long-random-secret",
    "changeme",
    "secret",
})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),   # look in cwd first, then parent (Docker Compose)
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    # IMPORTANT: must include "+asyncpg" driver prefix for async operation.
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/sysdesign_db"

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "changeme-replace-with-a-long-random-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── OAuth — Google ────────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/callback/google"

    # ── OAuth — GitHub ────────────────────────────────────────────────────────
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/auth/callback/github"

    # ── App ───────────────────────────────────────────────────────────────────
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    FRONTEND_URL: str = "http://localhost:5173"
    DEBUG: bool = True

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Improvement #9: Enforce asyncpg scheme at startup, not at first DB call."""
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use 'postgresql+asyncpg://' scheme for async "
                f"SQLAlchemy operation. Got: {v!r}"
            )
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Improvement #2: Reject weak or placeholder JWT secrets at startup."""
        if len(v) < 32:
            raise ValueError(
                f"JWT_SECRET_KEY must be at least 32 characters (got {len(v)}). "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if v in _WEAK_JWT_SECRETS:
            raise ValueError(
                "JWT_SECRET_KEY is set to a known placeholder value. "
                "Set a unique random secret in your .env file."
            )
        return v


settings = Settings()

