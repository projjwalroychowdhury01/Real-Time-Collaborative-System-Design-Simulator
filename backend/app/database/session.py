"""
Async SQLAlchemy session factory + database initialisation helper.

The engine is created lazily (on first use) so that importing this module
in tests does NOT immediately try to connect to a database or import asyncpg.
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# ── Lazy engine singleton ─────────────────────────────────────────────────────
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine() -> AsyncEngine:
    """Return (or lazily create) the shared async engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return (or lazily create) the shared session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a transactional async DB session.

    Improvement #7: commits on clean exit, rolls back on any exception,
    then re-raises so FastAPI error handlers can still return proper HTTP responses.
    """
    async with _get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """
    Create all tables defined in models.py if they do not already exist.

    In production this is replaced by `alembic upgrade head`.
    This helper is kept so the app boots correctly out-of-the-box during
    Phase 1 development without requiring a manual migration step.
    """
    from app.database.models import Base  # local import to avoid circular refs
    async with _get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
