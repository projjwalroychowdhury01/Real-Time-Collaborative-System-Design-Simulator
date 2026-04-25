"""
Alembic migration environment — configured for async SQLAlchemy (asyncpg).

This file wires Alembic to:
  1. Read DATABASE_URL from app.config.settings (honours .env file).
  2. Import all ORM models so autogenerate detects schema changes.
  3. Use the async engine via run_sync for both offline and online modes.
"""
import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Make `app` importable from within the migrations/ directory ───────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings            # noqa: E402 — must be after sys.path fix
from app.database.models import Base      # noqa: E402 — imports all ORM models

# ── Alembic Config ────────────────────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url with the value from our pydantic settings so we
# don't have to duplicate it in alembic.ini.
# asyncpg cannot be used directly by Alembic's sync migration runner, so we
# swap the scheme to the plain psycopg2/asyncpg-compatible URL.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at our ORM metadata so `alembic revision --autogenerate` works.
target_metadata = Base.metadata


# ── Offline migrations ────────────────────────────────────────────────────────

def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations ─────────────────────────────────────────────────────────

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations via run_sync."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ── Entry point ───────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
