from __future__ import annotations

import logging
import fnmatch
from collections.abc import AsyncIterator

from redis.asyncio import Redis
import redis.exceptions

from app.core.config import get_settings

logger = logging.getLogger(__name__)

import time

class MockRedis:
    def __init__(self):
        self.data = {}
    
    async def get(self, key: str):
        record = self.data.get(key)
        if not record:
            return None
        if record['ex'] and time.time() > record['ex']:
            self.data.pop(key, None)
            return None
        return record['value']
    
    async def set(self, key: str, value: str, ex=None):
        self.data[key] = {
            'value': value,
            'ex': time.time() + ex if ex else None
        }
        
    async def delete(self, key: str):
        self.data.pop(key, None)
        
    async def exists(self, key: str):
        return 1 if key in self.data else 0
        
    async def incr(self, key: str):
        record = self.data.get(key)
        val = 0
        if record and (not record['ex'] or time.time() <= record['ex']):
            val = int(record['value'])
        
        self.data[key] = {
            'value': str(val + 1),
            'ex': record['ex'] if record else None
        }
        return val + 1
        
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
