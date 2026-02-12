from __future__ import annotations

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.core.rate_limit import check_rate_limit
from app.db.redis import get_redis
from app.schemas.auth import AuthenticatedUser
from app.api.deps.auth import get_current_active_user


async def rate_limit_login(request: Request, redis: Redis = Depends(get_redis)) -> None:
    """Rate limit login attempts per IP."""

    client_ip = request.client.host if request.client else "unknown"
    key = f"login:{client_ip}"
    await check_rate_limit(redis, key, max_requests=10, window_seconds=60)


async def rate_limit_booking_create(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    redis: Redis = Depends(get_redis),
) -> None:
    """Rate limit booking creation per user."""

    key = f"booking_create:user:{current_user.id}"
    await check_rate_limit(redis, key, max_requests=5, window_seconds=60)

