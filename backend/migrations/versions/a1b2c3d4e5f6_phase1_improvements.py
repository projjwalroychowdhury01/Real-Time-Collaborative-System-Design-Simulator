"""phase1_improvements

Revision ID: a1b2c3d4e5f6
Revises: 5f61c97975ba
Create Date: 2026-04-25

Applies Phase 1 improvements to an existing database:

Improvement #4 — Convert all TIMESTAMP columns to TIMESTAMPTZ
  Affected tables: users, designs, checkpoints,
                   collaboration_sessions, session_members

Improvement #6 — Add UNIQUE(session_id, user_id) constraint to session_members
  Prevents duplicate presence rows that corrupt active_users counts.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "5f61c97975ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Columns to convert per table: (table_name, column_name)
_TIMESTAMP_COLS: list[tuple[str, str]] = [
    ("users",                   "created_at"),
    ("users",                   "updated_at"),
    ("designs",                 "created_at"),
    ("designs",                 "updated_at"),
    ("checkpoints",             "created_at"),
    ("collaboration_sessions",  "created_at"),
    ("collaboration_sessions",  "expires_at"),
    ("session_members",         "joined_at"),
    ("session_members",         "last_heartbeat"),
]


def upgrade() -> None:
    # ── Improvement #4: TIMESTAMP → TIMESTAMPTZ ───────────────────────────────
    for table, col in _TIMESTAMP_COLS:
        op.alter_column(
            table,
            col,
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(timezone=False),
            existing_nullable=True,
            postgresql_using=f"{col} AT TIME ZONE 'UTC'",
        )

    # ── Improvement #6: composite unique constraint on session_members ────────
    op.create_unique_constraint(
        "uq_session_member",
        "session_members",
        ["session_id", "user_id"],
    )


def downgrade() -> None:
    # ── Revert #6 ─────────────────────────────────────────────────────────────
    op.drop_constraint("uq_session_member", "session_members", type_="unique")

    # ── Revert #4: TIMESTAMPTZ → TIMESTAMP ───────────────────────────────────
    for table, col in reversed(_TIMESTAMP_COLS):
        op.alter_column(
            table,
            col,
            type_=sa.DateTime(timezone=False),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=True,
        )
