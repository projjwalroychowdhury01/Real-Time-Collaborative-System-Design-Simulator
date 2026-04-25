"""
CRDT sync helpers.

In the MVP, the browser (Yjs) owns CRDT merging.
The server merely:
  1. Forwards binary Yjs updates between clients (via WebSocket manager).
  2. Persists the full Y.Doc state to PostgreSQL on each change.

This module contains helpers for that persistence step.
"""
from __future__ import annotations

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database.models import Design


async def persist_design_state(db: AsyncSession, design_id: int, design_json: dict) -> None:
    """Persist the latest merged design state to the DB (called after each CRDT update)."""
    await db.execute(
        update(Design)
        .where(Design.id == design_id)
        .values(design_json=design_json)
    )
    await db.commit()
