from __future__ import annotations

from datetime import datetime, timezone

from redis.asyncio import Redis


BLACKLIST_PREFIX = "jwt:blacklist:"


async def blacklist_token(redis: Redis, jti: str, exp_timestamp: int) -> None:
    """Store a token identifier (JTI) in Redis until its expiry.

    This supports a basic token blacklist for logout and admin revocation.
    """

    now_ts = int(datetime.now(timezone.utc).timestamp())
    ttl = max(exp_timestamp - now_ts, 0)
    key = f"{BLACKLIST_PREFIX}{jti}"
    # Using SET with EX to ensure automatic expiration
    await redis.set(key, "1", ex=ttl or 1)


async def is_token_blacklisted(redis: Redis, jti: str) -> bool:
    key = f"{BLACKLIST_PREFIX}{jti}"
    return bool(await redis.exists(key))

