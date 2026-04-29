"""
方圆智版 · 总闸 (入口文件)
文件路径: agent_api/src/service.py
"""

import logging
import warnings
from contextlib import asynccontextmanager
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from langchain_core._api import LangChainBetaWarning
from langfuse import Langfuse

from agents import get_agent, get_all_agent_info, load_agent
from core import settings
from core.postgres import get_postgres_saver, get_postgres_store
from src.api.routers import agent, files_admin, vector_admin

warnings.filterwarnings("ignore", category=LangChainBetaWarning)
logger = logging.getLogger("uvicorn")


def custom_generate_unique_id(route: APIRoute) -> str:
    return route.name


# ==============================================================================
# 🔑 JWKS 客户端单例：启动时预热，自动缓存公钥，kid 不匹配时自动重拉
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
# 🛡️ 核心安保：Bearer 令牌验证器
# 优先级：JWKS 动态公钥(RS256) > AUTH_SECRET 兜底 > 匿名(仅开发)
# ==============================================================================
def verify_bearer(
    http_auth: Annotated[
        HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))
    ],
) -> dict:
    """
    验证 Bearer token，返回解密后的用户 payload。
    供下游路由通过 Depends(verify_bearer) 获取当前用户身份。
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
            # token header 里的 kid 自动寻址，缓存未命中时重新拉取 JWKS
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
        return {"user": "admin", "auth_mode": "secret"}

    # ── 兜底：未配置任何鉴权（仅开发环境）──────────────────────────────────
    logger.warning("⚠️ 未配置鉴权，以匿名模式放行（请勿在生产环境使用）")
    return {"user": "anonymous", "auth_mode": "none"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """资源预热：连数据库、加载所有 Agent 插件"""
    # 启动时预热 JWKS，避免首个请求冷启动
    get_jwks_client()

    try:
        async with get_postgres_saver() as saver, get_postgres_store() as store:
            if hasattr(saver, "setup"):
                await saver.setup()
            if hasattr(store, "setup"):
                await store.setup()

            for a in get_all_agent_info():
                try:
                    await load_agent(a.key)
                    loaded_agent = get_agent(a.key)
                    loaded_agent.checkpointer = saver
                    loaded_agent.store = store
                    logger.info(f"Agent {a.key} 已成功挂载记忆体")
                except Exception as e:
                    logger.error(f"Failed to load agent {a.key}: {e}")
            yield
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        raise


# ==============================================================================
# 1. 实例化地基
# ==============================================================================
app = FastAPI(lifespan=lifespan, generate_unique_id_function=custom_generate_unique_id)


# ==============================================================================
# 2. 挂载中间件
# ==============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# 3. 基础健康检查（公开，无需鉴权）
# ==============================================================================
@app.get("/health", tags=["System"])
async def health_check():
    health_status = {"status": "ok"}
    if settings.LANGFUSE_TRACING:
        try:
            health_status["langfuse"] = (
                "connected" if Langfuse().auth_check() else "disconnected"
            )
        except Exception:
            health_status["langfuse"] = "disconnected"
    return health_status


# ==============================================================================
# 4. 注册子路由（统一 Bearer 鉴权保护）
# ==============================================================================

# AI 宇宙：处理对话、流式输出、反馈
app.include_router(agent.router, dependencies=[Depends(verify_bearer)])

# 向量管理宇宙：处理入库任务、查询向量切片、监控任务状态
app.include_router(vector_admin.router, dependencies=[Depends(verify_bearer)])

# 文件管理宇宙：处理物理源文件的增删改查
app.include_router(files_admin.router, dependencies=[Depends(verify_bearer)])