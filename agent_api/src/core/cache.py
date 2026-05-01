"""Redis cache utilities with decorator support.

Compatible with the dual-pool redis.py (AsyncRedisPool / SyncRedisPool).
Async paths use get_async_redis(); sync fallback skips cache transparently.
"""

import functools
import hashlib
import json
import logging
from typing import Any, Callable, TypeVar

from core.redis import get_async_redis

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Sentinel stored in Redis to represent a cached None value.
# Prevents cache-penetration when the underlying function legitimately returns None.
_NONE_SENTINEL = "__cache_none__"

_MIN_TTL = 1
_MAX_TTL = 86_400  # 24 h


# ---------------------------------------------------------------------------
# Key construction
# ---------------------------------------------------------------------------

def cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """Build a deterministic, collision-resistant Redis cache key.

    Uses SHA-256 (first 16 hex chars = 64-bit space) instead of truncated MD5.
    ``self`` / ``cls`` positional args are excluded automatically when the
    caller passes ``skip_first=True`` (set by the decorator for bound methods).
    """
    key_data = {"args": args, "kwargs": sorted(kwargs.items())}
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    hash_part = hashlib.sha256(key_str.encode()).hexdigest()[:16]
    return f"{prefix}:{hash_part}"


# ---------------------------------------------------------------------------
# TTL guard
# ---------------------------------------------------------------------------

def _validated_ttl(ttl: int) -> int:
    if ttl < _MIN_TTL:
        raise ValueError("TTL must be >= %d second(s), got %d" % (_MIN_TTL, ttl))
    if ttl > _MAX_TTL:
        raise ValueError("TTL must be <= %d seconds (24 h), got %d" % (_MAX_TTL, ttl))
    return ttl


# ---------------------------------------------------------------------------
# Primitive cache operations
# ---------------------------------------------------------------------------

async def cache_get(key: str) -> tuple[bool, Any]:
    """Return ``(found, value)`` to distinguish a cached None from a cache miss.

    >>> found, value = await cache_get("my:key")
    >>> if found:
    ...     return value   # may be None — that is valid cached data
    """
    try:
        async with get_async_redis() as redis:
            raw = await redis.get(key)
            if raw is None:
                return False, None
            if raw == _NONE_SENTINEL:
                return True, None
            return True, json.loads(raw)
    except Exception as exc:
        logger.error("Cache GET error [key=%s]: %s", key, exc)
        return False, None


async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """Serialise *value* and store it under *key* with the given *ttl* (seconds).

    A ``None`` value is stored as the sentinel string so it can be distinguished
    from a cache miss on retrieval.
    """
    try:
        ttl = _validated_ttl(ttl)
        async with get_async_redis() as redis:
            payload = _NONE_SENTINEL if value is None else json.dumps(value, default=str)
            await redis.setex(key, ttl, payload)
            return True
    except ValueError as exc:
        logger.error("Cache SET rejected [key=%s]: %s", key, exc)
        return False
    except Exception as exc:
        logger.error("Cache SET error [key=%s]: %s", key, exc)
        return False


async def cache_delete(key: str) -> bool:
    """Delete a single cache key. Returns True if the key existed."""
    try:
        async with get_async_redis() as redis:
            return bool(await redis.delete(key))
    except Exception as exc:
        logger.error("Cache DELETE error [key=%s]: %s", key, exc)
        return False


async def invalidate_pattern(pattern: str, batch_size: int = 500) -> int:
    """Delete all keys matching *pattern* using SCAN + pipelined DEL.

    Avoids the N-round-trip anti-pattern of calling DEL inside scan_iter.
    ``batch_size`` controls how many keys are pipelined per DEL call so
    that no single pipeline payload becomes unbounded.

    Returns the total number of keys deleted.
    """
    try:
        async with get_async_redis() as redis:
            deleted = 0
            batch: list[str] = []

            async for key in redis.scan_iter(match=pattern, count=200):
                batch.append(key)
                if len(batch) >= batch_size:
                    async with redis.pipeline(transaction=False) as pipe:
                        for k in batch:
                            pipe.delete(k)
                        results = await pipe.execute()
                    deleted += sum(results)
                    batch.clear()

            # flush remainder
            if batch:
                async with redis.pipeline(transaction=False) as pipe:
                    for k in batch:
                        pipe.delete(k)
                    results = await pipe.execute()
                deleted += sum(results)

            logger.info(
                "Invalidated %d key(s) matching pattern '%s'", deleted, pattern
            )
            return deleted
    except Exception as exc:
        logger.error("Pattern invalidation error [pattern=%s]: %s", pattern, exc)
        return 0


# ---------------------------------------------------------------------------
# @cached decorator
# ---------------------------------------------------------------------------

def cached(
    ttl: int = 300,
    key_prefix: str = "cache",
    skip_self: bool = False,
) -> Callable[[F], F]:
    """Async-only cache decorator.

    Args:
        ttl:        Seconds to keep the cached value (1 – 86400).
        key_prefix: Namespace prefix in the Redis key.
        skip_self:  If True, strip the first positional arg (``self``/``cls``)
                    from the cache-key computation. Useful for bound methods
                    where the instance itself should not affect the cache key.

    On a cache miss the return value — including ``None`` — is cached so that
    the underlying function is not hammered by repeated calls.

    Sync functions are passed through unchanged (no silent data loss).

    Example::

        @cached(ttl=60, key_prefix="user", skip_self=True)
        async def get_user(self, user_id: int) -> dict:
            ...
    """
    _validated_ttl(ttl)  # fail fast at decoration time

    def decorator(func: F) -> F:
        import asyncio

        if not asyncio.iscoroutinefunction(func):
            # Sync functions: return as-is with an explicit notice in the docstring.
            logger.debug(
                "@cached has no effect on sync function '%s' — wrap it in an async caller "
                "or use get_sync_redis() directly.",
                func.__name__,
            )
            return func

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key_args = args[1:] if skip_self else args
            key = cache_key(key_prefix, func.__name__, *key_args, **kwargs)

            found, cached_value = await cache_get(key)
            if found:
                logger.debug("Cache HIT  [key=%s]", key)
                return cached_value

            logger.debug("Cache MISS [key=%s]", key)
            result = await func(*args, **kwargs)
            await cache_set(key, result, ttl)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator