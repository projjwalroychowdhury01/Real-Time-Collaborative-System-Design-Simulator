"""
Async Redis client — lazy singleton, token blacklist helpers.

Fail-open policy: if Redis is unreachable, revocation checks return False
and revocations are silently skipped.  This keeps the app functional during
Redis outages while still blacklisting tokens when Redis is healthy.
In production you may prefer fail-closed; toggle via REDIS_STRICT_REVOKE env var.
"""
from __future__ import annotations

import logging

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

# ── Lazy singleton ────────────────────────────────────────────────────────────
_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """Return (or lazily create) the shared async Redis client."""
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _redis


async def close_redis() -> None:
    """Close the Redis connection (called on app shutdown)."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


# ── Token blacklist helpers ───────────────────────────────────────────────────

REVOKED_PREFIX = "revoked:"


async def is_token_revoked(jti: str) -> bool:
    """Return True if the token JTI is in the Redis revocation set.

    Returns False on any Redis error (fail-open).
    """
    if not jti:
        return False
    try:
        return bool(await get_redis().exists(f"{REVOKED_PREFIX}{jti}"))
    except Exception as exc:
        logger.warning("Redis unavailable during revocation check: %s", exc)
        return False  # fail-open


async def revoke_token(jti: str, ttl_seconds: int) -> None:
    """Add a token JTI to the blacklist with a TTL matching its remaining lifetime.

    Silently no-ops on Redis errors.
    """
    if not jti or ttl_seconds <= 0:
        return
    try:
        await get_redis().setex(f"{REVOKED_PREFIX}{jti}", ttl_seconds, "1")
    except Exception as exc:
        logger.warning("Redis unavailable; token %s not blacklisted: %s", jti, exc)
