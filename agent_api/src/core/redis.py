"""Redis connection pool and client management."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from core.config import settings

logger = logging.getLogger(__name__)


class RedisPool:
    """Async Redis connection pool manager."""

    _instance: Redis | None = None
    _pool: ConnectionPool | None = None

    @classmethod
    async def initialize(cls) -> None:
        """Initialize the Redis connection pool."""
        if cls._instance is not None:
            logger.warning("Redis pool already initialized")
            return

        try:
            cls._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True,
            )
            cls._instance = Redis(connection_pool=cls._pool)

            # Test connection
            await cls._instance.ping()
            logger.info(f"Redis pool initialized: {settings.REDIS_URL}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis pool: {e}")
            raise

    @classmethod
    async def close(cls) -> None:
        """Close the Redis connection pool."""
        if cls._instance is not None:
            await cls._instance.close()
            cls._instance = None
            cls._pool = None
            logger.info("Redis pool closed")

    @classmethod
    def get_client(cls) -> Redis:
        """Get the Redis client instance."""
        if cls._instance is None:
            raise RuntimeError("Redis pool not initialized. Call initialize() first.")
        return cls._instance


@asynccontextmanager
async def get_redis() -> AsyncGenerator[Redis, None]:
    """Get a Redis client from the pool as an async context manager."""
    client = RedisPool.get_client()
    try:
        yield client
    except Exception as e:
        logger.error(f"Redis operation error: {e}")
        raise


async def health_check() -> bool:
    """Check Redis connectivity."""
    try:
        client = RedisPool.get_client()
        return await client.ping()
    except Exception:
        return False
