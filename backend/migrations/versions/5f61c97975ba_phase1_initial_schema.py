"""phase1_initial_schema

Revision ID: 5f61c97975ba
Revises: 
Create Date: 2026-04-25

Creates all 5 tables for Phase 1:
  - users
  - designs
  - checkpoints
  - collaboration_sessions
  - session_members
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "5f61c97975ba"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Phase 1 schema."""

    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",            sa.Integer(),     primary_key=True),
        sa.Column("email",         sa.String(255),   nullable=False,  unique=True),
        sa.Column("username",      sa.String(128),   nullable=False,  unique=True),
        sa.Column("auth_provider", sa.String(50),    nullable=True),
        sa.Column("auth_id",       sa.String(255),   nullable=True,   unique=True),
        sa.Column("created_at",    sa.DateTime(),    server_default=sa.func.now()),
        sa.Column("updated_at",    sa.DateTime(),    server_default=sa.func.now()),
    )

    # ── designs ──────────────────────────────────────────────────────────────
    op.create_table(
        "designs",
        sa.Column("id",          sa.Integer(),    primary_key=True),
        sa.Column("user_id",     sa.Integer(),    sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name",        sa.String(255),  nullable=False),
        sa.Column("description", sa.Text(),       nullable=True),
        sa.Column("design_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_public",   sa.Boolean(),    server_default="false"),
        sa.Column("created_at",  sa.DateTime(),   server_default=sa.func.now()),
        sa.Column("updated_at",  sa.DateTime(),   server_default=sa.func.now()),
    )
    op.create_index("idx_designs_user_id", "designs", ["user_id"])

    # ── checkpoints ──────────────────────────────────────────────────────────
    op.create_table(
        "checkpoints",
        sa.Column("id",                sa.Integer(),   primary_key=True),
        sa.Column("design_id",         sa.Integer(),   sa.ForeignKey("designs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("checkpoint_number", sa.Integer(),   nullable=False),
        sa.Column("design_json",       postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata",          postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at",        sa.DateTime(),  server_default=sa.func.now()),
    )
    op.create_index("idx_checkpoints_design_id", "checkpoints", ["design_id"])

    # ── collaboration_sessions ───────────────────────────────────────────────
    op.create_table(
        "collaboration_sessions",
        sa.Column("id",            sa.Integer(),     primary_key=True),
        sa.Column("design_id",     sa.Integer(),     sa.ForeignKey("designs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_token", sa.String(255),   nullable=False, unique=True),
        sa.Column("creator_id",    sa.Integer(),     sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at",    sa.DateTime(),    server_default=sa.func.now()),
        sa.Column("expires_at",    sa.DateTime(),    nullable=True),
        sa.Column("active_users",  sa.Integer(),     server_default="0"),
    )
    op.create_index("idx_sessions_token", "collaboration_sessions", ["session_token"])

    # ── session_members ──────────────────────────────────────────────────────
    op.create_table(
        "session_members",
        sa.Column("id",             sa.Integer(),   primary_key=True),
        sa.Column("session_id",     sa.Integer(),   sa.ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id",        sa.Integer(),   sa.ForeignKey("users.id"), nullable=False),
        sa.Column("joined_at",      sa.DateTime(),  server_default=sa.func.now()),
        sa.Column("cursor_x",       sa.Float(),     nullable=True),
        sa.Column("cursor_y",       sa.Float(),     nullable=True),
        sa.Column("last_heartbeat", sa.DateTime(),  nullable=True),
    )


def downgrade() -> None:
    """Drop Phase 1 schema in reverse dependency order."""
    op.drop_table("session_members")
    op.drop_index("idx_sessions_token",       table_name="collaboration_sessions")
    op.drop_table("collaboration_sessions")
    op.drop_index("idx_checkpoints_design_id", table_name="checkpoints")
    op.drop_table("checkpoints")
    op.drop_index("idx_designs_user_id",       table_name="designs")
    op.drop_table("designs")
    op.drop_table("users")
