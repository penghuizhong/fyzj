"""Redis cache utilities with decorator support."""

import functools
import hashlib
import json
import logging
from typing import Any, Callable, TypeVar

from core.redis import get_redis

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items()),
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    hash_part = hashlib.md5(key_str.encode()).hexdigest()[:12]
    return f"{prefix}:{hash_part}"


async def cache_get(key: str) -> Any | None:
    try:
        async with get_redis() as redis:
            value = await redis.get(key)
            if value:
                return json.loads(value)
            return None
    except Exception as e:
        logger.error(f"Cache get error for key {key}: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    try:
        async with get_redis() as redis:
            serialized = json.dumps(value, default=str)
            await redis.setex(key, ttl, serialized)
            return True
    except Exception as e:
        logger.error(f"Cache set error for key {key}: {e}")
        return False


async def cache_delete(key: str) -> bool:
    try:
        async with get_redis() as redis:
            result = await redis.delete(key)
            return result > 0
    except Exception as e:
        logger.error(f"Cache delete error for key {key}: {e}")
        return False


async def invalidate_pattern(pattern: str) -> int:
    try:
        async with get_redis() as redis:
            deleted = 0
            async for key in redis.scan_iter(match=pattern):
                await redis.delete(key)
                deleted += 1
            logger.info(f"Invalidated {deleted} keys matching pattern: {pattern}")
            return deleted
    except Exception as e:
        logger.error(f"Pattern invalidation error for {pattern}: {e}")
        return 0


def cached(ttl: int = 300, key_prefix: str = "cache") -> Callable[[F], F]:
    def decorator(func: F) -> F:
        import asyncio

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = cache_key(key_prefix, func.__name__, *args, **kwargs)

            cached_value = await cache_get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {key}")
                return cached_value

            result = await func(*args, **kwargs)
            await cache_set(key, result, ttl)
            logger.debug(f"Cache miss: {key}")
            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.warning(f"Cache decorator on sync function {func.__name__}")
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
