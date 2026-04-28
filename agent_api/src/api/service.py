"""
方圆智版 · 总闸 (入口文件)
文件路径: agent_api/src/service.py
"""

import logging
import warnings
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.routing import APIRoute
from langchain_core._api import LangChainBetaWarning

# 🌟 新增 JWT 解析库
from jose import jwt, JWTError

from src.api.routers import vector_admin, files_admin, agent
from core import settings
from core.postgres import get_postgres_saver, get_postgres_store
from agents import get_all_agent_info, load_agent, get_agent
from langfuse import Langfuse

warnings.filterwarnings("ignore", category=LangChainBetaWarning)
logger = logging.getLogger("uvicorn")


def custom_generate_unique_id(route: APIRoute) -> str:
    return route.name


# ==============================================================================
# 🛡️ 核心安保：双轨制 Bearer 令牌验证器 (JWT RS256 / Secret)
# ==============================================================================
def verify_bearer(
    http_auth: Annotated[
        HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))
    ],
) -> dict:
    """
    升级版：不仅验证真伪，还会返回解密后的用户信息 payload。
    供下游路由获取当前请求的用户身份。
    """
    # 1. 兜底方案：如果没设公钥，走简单的 Secret 对暗号逻辑
    if not settings.JWT_PUBLIC_KEY:
        if settings.AUTH_SECRET:
            if not http_auth or http_auth.credentials != settings.AUTH_SECRET.get_secret_value():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Secret Token"
                )
            return {"user": "admin", "auth_mode": "secret"}
        return {"user": "anonymous", "auth_mode": "none"}

    # 2. 核心方案：大厂级 JWT (RS256) 验证
    if not http_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization Header"
        )

    try:
        # 核心解密引擎：使用公钥验证数字签名
        # options={"verify_aud": False} 允许不验证audience，因为不同client可能有不同的aud
        payload = jwt.decode(
            http_auth.credentials,
            settings.JWT_PUBLIC_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        # 解密成功！payload 里通常包含 {"sub": "user_123", "exp": 171...}
        return payload
    except JWTError as e:
        logger.warning(f"🛡️ JWT 拦截非法请求: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌无效、遭篡改或已过期"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """资源预热：连数据库、加载所有 Agent 插件"""
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


# 1. 实例化地基
app = FastAPI(lifespan=lifespan, generate_unique_id_function=custom_generate_unique_id)

# 2. 挂载中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议改回具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 3. 基础健康检查接口
@app.get("/health", tags=["System"])
async def health_check():
    health_status = {"status": "ok"}
    if settings.LANGFUSE_TRACING:
        try:
            health_status["langfuse"] = "connected" if Langfuse().auth_check() else "disconnected"
        except Exception:
            health_status["langfuse"] = "disconnected"
    return health_status


# ==============================================================================
# 🌟 终极注册：必须放在最后！
# 这里才是真正的“开门营业”，统一挂载三个子宇宙并开启 Bearer 鉴权保护
# ==============================================================================

# AI 宇宙：处理对话、流式输出、反馈
app.include_router(agent.router, dependencies=[Depends(verify_bearer)])

# 向量管理宇宙：处理入库任务、查询向量切片、监控任务状态
app.include_router(vector_admin.router, dependencies=[Depends(verify_bearer)])

# 文件管理宇宙：处理物理源文件的增删改查
app.include_router(files_admin.router, dependencies=[Depends(verify_bearer)])
