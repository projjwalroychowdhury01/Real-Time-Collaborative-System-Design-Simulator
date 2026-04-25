"""
JWT session management, refresh token handling, and user helpers.

Token strategy
--------------
* Access token  — short-lived (default 60 min), used on every API request.
* Refresh token — long-lived (default 7 days), used to obtain a new access token
  without re-authenticating via OAuth.  Stored client-side (httpOnly cookie or
  secure local storage).  Server-side blacklisting can be added in Phase 2 via
  a Redis SET of revoked JTIs.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from jose import jwt, JWTError
from fastapi import Cookie, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database.models import User
from app.database.session import get_db

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
# FastAPI dependency: current user
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the Bearer token to an authenticated User record."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials, expected_type="access")
    user_id = int(payload.get("sub", 0))

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Refresh token endpoint helper
# ---------------------------------------------------------------------------

async def refresh_access_token(refresh_token: str, db: AsyncSession) -> dict:
    """Validate a refresh token and issue a new access token."""
    payload = decode_token(refresh_token, expected_type="refresh")
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
# User upsert helper (used by OAuth callbacks)
# ---------------------------------------------------------------------------

async def get_or_create_user(
    db: AsyncSession,
    *,
    email: str,
    username: str,
    provider: str,
    auth_id: str,
) -> User:
    """Return existing user or create a new one.  Guarantees username uniqueness."""
    # Try to find by OAuth identity first
    result = await db.execute(select(User).where(User.auth_id == auth_id))
    user = result.scalar_one_or_none()
    if user:
        return user

    # Ensure username is unique by appending a numeric suffix if needed
    base = username
    suffix = 0
    while True:
        check = await db.execute(select(User).where(User.username == username))
        if not check.scalar_one_or_none():
            break
        suffix += 1
        username = f"{base}{suffix}"

    user = User(email=email, username=username, auth_provider=provider, auth_id=auth_id)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
