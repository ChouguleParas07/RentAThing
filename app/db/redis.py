from __future__ import annotations

import logging
import fnmatch
from collections.abc import AsyncIterator

from redis.asyncio import Redis
import redis.exceptions

from app.core.config import get_settings

logger = logging.getLogger(__name__)

class MockRedis:
    def __init__(self):
        self.data = {}
    
    async def get(self, key: str):
        return self.data.get(key)
    
    async def set(self, key: str, value: str, ex=None):
        self.data[key] = value
        
    async def delete(self, key: str):
        self.data.pop(key, None)
        
    async def exists(self, key: str):
        return 1 if key in self.data else 0
        
    async def incr(self, key: str):
        val = self.data.get(key, 0)
        self.data[key] = int(val) + 1
        return self.data[key]
        
    async def expire(self, key: str, time):
        pass
        
    async def scan_iter(self, match: str = "*"):
        for key in list(self.data.keys()):
            if match:
                if fnmatch.fnmatch(key, match):
                    yield key
            else:
                yield key

def get_redis_client() -> Redis:
    """Create a global async Redis client.

    We use this for token blacklisting, rate limiting and caching.
    """
    settings = get_settings()
    return Redis.from_url(str(settings.redis_url), encoding="utf-8", decode_responses=True)


redis_client: Redis = get_redis_client()
mock_redis_client = MockRedis()

async def get_redis() -> AsyncIterator[Redis]:
    """FastAPI dependency for Redis. Falls back to MockRedis if Redis is unreachable."""
    try:
        await redis_client.ping()
        yield redis_client
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
        logger.warning("Redis is unreachable. Using MockRedis in-memory store for local dev.")
        yield mock_redis_client # type: ignore
    finally:
        pass
