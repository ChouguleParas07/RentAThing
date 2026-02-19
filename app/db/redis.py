from __future__ import annotations

from collections.abc import AsyncIterator

from redis.asyncio import Redis

from app.core.config import get_settings


settings = get_settings()


def get_redis_client() -> Redis:
    """Create a global async Redis client.

    We use this for token blacklisting, rate limiting and caching.
    """

    return Redis.from_url(str(settings.redis_url), encoding="utf-8", decode_responses=True)


redis_client: Redis = get_redis_client()


async def get_redis() -> AsyncIterator[Redis]:
    """FastAPI dependency for Redis."""

    try:
        yield redis_client
    finally:
        # We do not close the global client per-request; connection pooling is handled internally.
        # This function mainly exists to keep a consistent DI pattern.
        pass

