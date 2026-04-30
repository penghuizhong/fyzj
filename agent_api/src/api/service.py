"""
方圆智版 · 总闸 (入口文件)
文件路径: agent_api/src/api/service.py
"""

import logging
import warnings
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from langchain_core._api import LangChainBetaWarning
from langfuse import Langfuse

from agents import get_agent, get_all_agent_info, load_agent
from api.deps import get_jwks_client           # JWKS 预热
from core import settings
from core.postgres import get_postgres_saver, get_postgres_store
from src.api.routers import agent, files_admin, vector_admin

warnings.filterwarnings("ignore", category=LangChainBetaWarning)
logger = logging.getLogger("uvicorn")


def custom_generate_unique_id(route: APIRoute) -> str:
    return route.name


@asynccontextmanager
async def lifespan(app: FastAPI):
    """资源预热：JWKS 公钥、数据库连接、Agent 插件"""
    # 预热 JWKS，避免首个请求冷启动去拉公钥
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
# 4. 注册子路由
# 鉴权由各路由函数内的 CurrentUser 依赖承担，此处无需 dependencies
# ==============================================================================
app.include_router(agent.router)
app.include_router(vector_admin.router)
app.include_router(files_admin.router)