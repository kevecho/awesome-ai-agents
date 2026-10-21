"""
Redis cache utility for session storage and rate limiting.

Provides async Redis client wrapper with common caching patterns.
"""

from typing import Any, Optional
import json

import redis.asyncio as redis

from app.core.config import settings

_pool: Optional[redis.ConnectionPool] = None


async def get_redis() -> redis.Redis:
    """Get or create an async Redis connection from the pool."""
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD or None,
            max_connections=20,
        )
    return redis.Redis(connection_pool=_pool)


async def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache, deserializing JSON."""
    client = await get_redis()
    value = await client.get(key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value.decode("utf-8") if isinstance(value, bytes) else value


async def cache_set(key: str, value: Any, ttl: int = 3600) -> None:
    """Set a cache value with TTL, serializing to JSON."""
    client = await get_redis()
    serialized = json.dumps(value, default=str, ensure_ascii=False)
    await client.setex(key, ttl, serialized)


async def cache_delete(key: str) -> None:
    """Delete a cache key."""
    client = await get_redis()
    await client.delete(key)


async def cache_exists(key: str) -> bool:
    """Check if a key exists in cache."""
    client = await get_redis()
    return await client.exists(key) > 0


async def increment_counter(key: str, ttl: int = 60) -> int:
    """Increment a counter, setting TTL on first increment. Returns new count."""
    client = await get_redis()
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, ttl)
    return count


async def close_redis_pool() -> None:
    """Close the Redis connection pool on shutdown."""
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None
