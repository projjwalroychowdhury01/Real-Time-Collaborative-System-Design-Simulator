"""
SQLAlchemy ORM models mirroring schema.sql.

Improvements applied:
  #4 — All timestamp columns use DateTime(timezone=True) (TIMESTAMPTZ in PostgreSQL)
       to avoid silent UTC vs local-time confusion across deployments.
  #6 — session_members has a composite UniqueConstraint(session_id, user_id)
       to prevent duplicate presence rows that corrupt active_users counts.
"""
from sqlalchemy import (
    Boolean, Column, Float, ForeignKey, Integer, String,
    Text, DateTime, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True)
    email         = Column(String(255), unique=True, nullable=False)
    username      = Column(String(128), unique=True, nullable=False)
    auth_provider = Column(String(50))
    auth_id       = Column(String(255), unique=True)
    # Improvement #4: timezone-aware timestamps
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    designs  = relationship("Design", back_populates="owner", cascade="all, delete")


class Design(Base):
    __tablename__ = "designs"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name        = Column(String(255), nullable=False)
    description = Column(Text)
    design_json = Column(JSONB)
    is_public   = Column(Boolean, default=False)
    # Improvement #4: timezone-aware timestamps
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner       = relationship("User", back_populates="designs")
    checkpoints = relationship("Checkpoint", back_populates="design", cascade="all, delete")
    sessions    = relationship("CollaborationSession", back_populates="design", cascade="all, delete")


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id                = Column(Integer, primary_key=True)
    design_id         = Column(Integer, ForeignKey("designs.id", ondelete="CASCADE"), nullable=False)
    checkpoint_number = Column(Integer, nullable=False)
    design_json       = Column(JSONB)
    checkpoint_meta   = Column("metadata", JSONB)   # `metadata` is reserved by SQLAlchemy
    # Improvement #4: timezone-aware timestamp
    created_at        = Column(DateTime(timezone=True), server_default=func.now())

    design = relationship("Design", back_populates="checkpoints")


class CollaborationSession(Base):
    __tablename__ = "collaboration_sessions"

    id            = Column(Integer, primary_key=True)
    design_id     = Column(Integer, ForeignKey("designs.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    creator_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Improvement #4: timezone-aware timestamps
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    expires_at    = Column(DateTime(timezone=True))
    active_users  = Column(Integer, default=0)

    design  = relationship("Design", back_populates="sessions")
    members = relationship("SessionMember", back_populates="session", cascade="all, delete")


class SessionMember(Base):
    __tablename__ = "session_members"
    # Improvement #6: prevent duplicate presence rows for the same user in a session
    __table_args__ = (
        UniqueConstraint("session_id", "user_id", name="uq_session_member"),
    )

    id             = Column(Integer, primary_key=True)
    session_id     = Column(Integer, ForeignKey("collaboration_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Improvement #4: timezone-aware timestamps
    joined_at      = Column(DateTime(timezone=True), server_default=func.now())
    cursor_x       = Column(Float)
    cursor_y       = Column(Float)
    last_heartbeat = Column(DateTime(timezone=True))

    session = relationship("CollaborationSession", back_populates="members")
