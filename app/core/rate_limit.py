from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from redis.asyncio import Redis


async def check_rate_limit(
    redis: Redis,
    key: str,
    max_requests: int,
    window_seconds: int = 60,
) -> None:
    """Simple fixed-window rate limiter using Redis INCR/EXPIRE."""

    now = int(datetime.utcnow().timestamp())
    window_key = f"ratelimit:{key}:{now // window_seconds}"
    current = await redis.incr(window_key)
    if current == 1:
        await redis.expire(window_key, window_seconds)

    if current > max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )

