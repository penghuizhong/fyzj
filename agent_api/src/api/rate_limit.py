"""
Rate limiting configuration with Redis storage.
文件路径: agent_api/src/api/rate_limit.py
"""

import logging
from typing import Annotated

from fastapi import Request, Depends, HTTPException, status
from limits import parse
from limits.storage import RedisStorage
from limits.strategies import MovingWindowRateLimiter

from core import settings
from api.deps import verify_bearer  # 引入你写好的鉴权逻辑

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

async def check_rate_limit(
    request: Request,
    user_payload: Annotated[dict, Depends(verify_bearer)]  # 核心优化：直接在这里获取用户身份！
) -> None:
    """
    限流依赖项：复用 deps.py 中的鉴权结果进行限流
    """
    if not settings.RATE_LIMIT_ENABLED:
        return

    limiter = get_rate_limiter()
    user_id = user_payload.get("sub")
    auth_mode = user_payload.get("auth_mode")

    # 1. 确定限流的 Key 和 额度
    if user_id and auth_mode != "none":
        # 认证用户（走 JWKS 或 AUTH_SECRET）
        key = f"ratelimit:user:{user_id}"
        limit_str = settings.RATE_LIMIT_AUTHENTICATED
    else:
        # 匿名用户（开发环境无鉴权兜底）或解析失败
        forwarded = request.headers.get("X-Forwarded-For")
        ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        key = f"ratelimit:ip:{ip}"
        limit_str = settings.RATE_LIMIT_ANONYMOUS

    limit_item = parse(limit_str)

    # 2. 执行 Redis 扣减
    if not limiter.hit(limit_item, key):
        logger.warning(f"🚫 触发限流: {key} (额度: {limit_str})")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )