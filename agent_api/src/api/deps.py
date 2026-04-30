"""
依赖注入模块
文件路径: agent_api/src/api/deps.py
"""

import logging
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from core import settings

logger = logging.getLogger("uvicorn")

# ==============================================================================
# 🔑 JWKS 客户端单例：进程级缓存，kid 不匹配时自动重拉公钥
# ==============================================================================
_jwks_client: PyJWKClient | None = None


def get_jwks_client() -> PyJWKClient | None:
    global _jwks_client
    if _jwks_client is None and settings.CASDOOR_JWKS_URL:
        _jwks_client = PyJWKClient(
            settings.CASDOOR_JWKS_URL,
            cache_keys=True,
            lifespan=3600,
        )
        logger.info(f"🔑 JWKS 客户端已初始化: {settings.CASDOOR_JWKS_URL}")
    return _jwks_client


# ==============================================================================
# 🛡️ Bearer 令牌验证器
# 优先级：JWKS 动态公钥(RS256) > AUTH_SECRET 兜底 > 匿名(仅开发)
# ==============================================================================
def verify_bearer(
    http_auth: Annotated[
        HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))
    ],
) -> dict:
    """
    验证 Bearer token，返回解密后的用户 payload。
    供下游路由通过 Depends(verify_bearer) 或 CurrentUser 类型注入用户身份。
    """
    jwks = get_jwks_client()

    # ── 主路：JWKS 动态验证（RS256）──────────────────────────────────────────
    if jwks:
        if not http_auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization Header",
            )
        try:
            signing_key = jwks.get_signing_key_from_jwt(http_auth.credentials)
            payload = jwt.decode(
                http_auth.credentials,
                signing_key.key,
                algorithms=[settings.JWT_ALGORITHM],
                audience=settings.CASDOOR_CLIENT_ID or None,
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 已过期",
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"🛡️ JWT 拦截非法请求: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌无效或遭篡改",
            )

    # ── 降级路：AUTH_SECRET 简单对暗号（无 Casdoor 场景）────────────────────
    if settings.AUTH_SECRET:
        if (
            not http_auth
            or http_auth.credentials != settings.AUTH_SECRET.get_secret_value()
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Secret Token",
            )
        return {"sub": "admin", "auth_mode": "secret"}

    # ── 兜底：未配置任何鉴权（仅开发环境）──────────────────────────────────
    logger.warning("⚠️ 未配置鉴权，以匿名模式放行（请勿在生产环境使用）")
    return {"sub": "anonymous", "auth_mode": "none"}


# 类型别名：路由函数里直接用，省去重复写 Annotated[dict, Depends(verify_bearer)]
CurrentUser = Annotated[dict, Depends(verify_bearer)]