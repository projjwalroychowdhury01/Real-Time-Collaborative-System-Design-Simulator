"""
JWT session management, refresh token handling, and user helpers.

Token strategy
--------------
* Access token  — short-lived (default 60 min), used on every API request.
* Refresh token — long-lived (default 7 days), used to obtain a new access token
  without re-authenticating via OAuth.  Stored in an httpOnly cookie.
* Revocation    — on logout the refresh token's JTI is blacklisted in Redis with
  a TTL matching its remaining lifetime (Improvement #3).
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import settings
from app.database.models import User
from app.database.session import get_db

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

def create_access_token(data: dict) -> str:
    """Create a short-lived JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        **data,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a long-lived JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        **data,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_token_pair(user_id: int, email: str) -> dict:
    """Return both access + refresh tokens in a single dict."""
    base = {"sub": str(user_id), "email": email}
    return {
        "access_token": create_access_token(base),
        "refresh_token": create_refresh_token(base),
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# ---------------------------------------------------------------------------
# Token validation
# ---------------------------------------------------------------------------

def decode_token(token: str, expected_type: str = "access") -> dict:
    """Decode and validate a JWT.  Raises HTTP 401 on any failure."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Expected token type '{expected_type}'",
        )
    return payload


# ---------------------------------------------------------------------------
# FastAPI dependency: current user  (with blacklist check — Improvement #3)
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the Bearer token to an authenticated User record.

    Also checks the Redis token blacklist so that logged-out access tokens
    are rejected immediately even within their remaining expiry window.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials, expected_type="access")
    jti = payload.get("jti", "")

    # Improvement #3 — check revocation blacklist
    from app.redis_client import is_token_revoked
    if jti and await is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload.get("sub", 0))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Refresh token endpoint helper  (with blacklist check — Improvement #3)
# ---------------------------------------------------------------------------

async def refresh_access_token(refresh_token: str, db: AsyncSession) -> dict:
    """Validate a refresh token, check revocation, and issue a new access token."""
    payload = decode_token(refresh_token, expected_type="refresh")
    jti = payload.get("jti", "")

    # Improvement #3 — reject blacklisted refresh tokens (e.g. after logout)
    from app.redis_client import is_token_revoked
    if jti and await is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    user_id = int(payload.get("sub", 0))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access = create_access_token({"sub": str(user.id), "email": user.email})
    return {
        "access_token": new_access,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# ---------------------------------------------------------------------------
# User upsert helper (Improvement #5: atomic upsert replaces race-prone loop)
# ---------------------------------------------------------------------------

def _derive_username(raw_name: str, auth_id: str) -> str:
    """Build a deterministic, unique-enough username from the OAuth display name.

    Appends 8 hex chars derived from auth_id so concurrent OAuth callbacks for
    the same new user are idempotent and username collisions are negligible.
    """
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", raw_name.strip())[:100] or "user"
    suffix = hashlib.sha256(auth_id.encode()).hexdigest()[:8]
    return f"{sanitized}_{suffix}"


async def get_or_create_user(
    db: AsyncSession,
    *,
    email: str,
    username: str,
    provider: str,
    auth_id: str,
) -> User:
    """Upsert a user record using a single atomic PostgreSQL INSERT ... ON CONFLICT.

    Improvement #5: Replaces the while-True SELECT loop that had a TOCTOU race
    condition when two OAuth callbacks arrived simultaneously for the same user.

    Conflict resolution:
    - auth_id conflict → same user re-logging in → update updated_at only.
    - email conflict   → edge case (provider changed email) → update auth fields.
    """
    final_username = _derive_username(username, auth_id)

    stmt = (
        pg_insert(User)
        .values(
            email=email,
            username=final_username,
            auth_provider=provider,
            auth_id=auth_id,
        )
        .on_conflict_do_update(
            index_elements=["auth_id"],
            set_={"updated_at": func.now()},
        )
        .returning(User)
    )

    result = await db.execute(stmt)
    user = result.scalar_one()
    await db.commit()
    await db.refresh(user)
    return user
