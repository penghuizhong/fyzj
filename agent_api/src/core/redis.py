"""Redis connection pool and client management.

Provides both async (FastAPI) and sync (Celery) Redis clients
from a shared configuration, avoiding duplicate connections.
"""

import logging
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis as redis_sync
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio.connection import ConnectionPool as AsyncConnectionPool

from core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Async pool  (FastAPI / async routes)
# ---------------------------------------------------------------------------

class AsyncRedisPool:
    """Async Redis connection pool manager (singleton)."""

    _instance: AsyncRedis | None = None
    _pool: AsyncConnectionPool | None = None
    _lock = asyncio_lock = None  # replaced by init-time guard

    @classmethod
    async def initialize(cls) -> None:
        """Initialize the async Redis connection pool (idempotent)."""
        if cls._instance is not None:
            return  # already ready — no warning spam on multiple lifespan calls

        try:
            cls._pool = AsyncConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True,
            )
            cls._instance = AsyncRedis(connection_pool=cls._pool)
            await cls._instance.ping()
            logger.info("Async Redis pool initialized: %s", settings.REDIS_URL)
        except Exception as exc:
            logger.error("Failed to initialize async Redis pool: %s", exc)
            cls._instance = None
            cls._pool = None
            raise

    @classmethod
    async def close(cls) -> None:
        """Gracefully close the async Redis connection pool."""
        if cls._instance is not None:
            await cls._instance.aclose()
            if cls._pool is not None:
                await cls._pool.aclose()
            cls._instance = None
            cls._pool = None
            logger.info("Async Redis pool closed")

    @classmethod
    def get_client(cls) -> AsyncRedis:
        """Return the shared async Redis client."""
        if cls._instance is None:
            raise RuntimeError(
                "Async Redis pool not initialized. Call AsyncRedisPool.initialize() first."
            )
        return cls._instance


@asynccontextmanager
async def get_async_redis() -> AsyncGenerator[AsyncRedis, None]:
    """Yield the shared async Redis client (does NOT close on exit — pool is shared)."""
    client = AsyncRedisPool.get_client()
    try:
        yield client
    except Exception as exc:
        logger.error("Async Redis operation error: %s", exc)
        raise


async def async_health_check() -> bool:
    """Verify async Redis connectivity."""
    try:
        return bool(await AsyncRedisPool.get_client().ping())
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Sync pool  (Celery tasks / sync code)
# ---------------------------------------------------------------------------

class SyncRedisPool:
    """Sync Redis connection pool manager (thread-safe singleton)."""

    _instance: redis_sync.Redis | None = None
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def initialize(cls) -> None:
        """Initialize the sync Redis connection pool (thread-safe, idempotent)."""
        if cls._instance is not None:
            return

        with cls._lock:
            if cls._instance is not None:  # double-checked locking
                return
            try:
                pool = redis_sync.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    max_connections=settings.REDIS_MAX_CONNECTIONS,
                    decode_responses=True,
                )
                client = redis_sync.Redis(connection_pool=pool)
                client.ping()  # validate connection at startup
                cls._instance = client
                logger.info("Sync Redis pool initialized: %s", settings.REDIS_URL)
            except Exception as exc:
                logger.error("Failed to initialize sync Redis pool: %s", exc)
                raise

    @classmethod
    def close(cls) -> None:
        """Close the sync Redis connection pool."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close()
                cls._instance = None
                logger.info("Sync Redis pool closed")

    @classmethod
    def get_client(cls) -> redis_sync.Redis:
        """Return the shared sync Redis client, auto-initializing if needed."""
        if cls._instance is None:
            cls.initialize()
        return cls._instance  # type: ignore[return-value]


def get_sync_redis() -> redis_sync.Redis:
    """Return the shared sync Redis client.

    Usage (Celery tasks):
        redis = get_sync_redis()
        redis.set("key", "value", ex=60)
    """
    return SyncRedisPool.get_client()


def sync_health_check() -> bool:
    """Verify sync Redis connectivity."""
    try:
        return bool(SyncRedisPool.get_client().ping())
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Unified health check
# ---------------------------------------------------------------------------

async def health_check() -> dict[str, bool]:
    """Return connectivity status for both async and sync clients."""
    return {
        "async": await async_health_check(),
        "sync": sync_health_check(),
    }