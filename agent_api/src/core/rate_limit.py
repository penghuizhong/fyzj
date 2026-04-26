"""Rate limiting configuration with Redis storage."""

import logging
from typing import Any

from fastapi import Request
from limits import parse
from limits.storage import RedisStorage
from limits.strategies import MovingWindowRateLimiter

from core import settings

logger = logging.getLogger(__name__)

_storage: RedisStorage | None = None
_limiter: MovingWindowRateLimiter | None = None


def get_rate_limit_storage() -> RedisStorage:
    global _storage
    if _storage is None:
        _storage = RedisStorage(settings.REDIS_URL)
    return _storage


def get_rate_limiter() -> MovingWindowRateLimiter:
    global _limiter
    if _limiter is None:
        storage = get_rate_limit_storage()
        _limiter = MovingWindowRateLimiter(storage)
    return _limiter


def get_limit_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"ratelimit:user:{user_id}"

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"

    return f"ratelimit:ip:{ip}"


class RateLimitMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        if not settings.RATE_LIMIT_ENABLED:
            await self.app(scope, receive, send)
            return

        limiter = get_rate_limiter()
        key = get_limit_key(request)

        # Check authentication status for appropriate limit
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            limit_str = settings.RATE_LIMIT_AUTHENTICATED
        else:
            limit_str = settings.RATE_LIMIT_ANONYMOUS

        limit_item = parse(limit_str)

        if not limiter.hit(limit_item, key):
            from starlette.responses import JSONResponse

            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
