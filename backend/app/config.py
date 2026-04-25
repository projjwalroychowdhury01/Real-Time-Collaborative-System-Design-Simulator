"""
Application configuration loaded from environment variables / .env file.

The DATABASE_URL must use the asyncpg driver scheme:
    postgresql+asyncpg://user:password@host:port/dbname

The .env file is loaded from the *backend/* working directory when running
`uvicorn app.main:app` directly, or from the root when using Docker Compose
via `env_file: .env`.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


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


settings = Settings()
