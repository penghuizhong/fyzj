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
from api.deps import get_jwks_client
from core import settings
from core.postgres import get_postgres_saver, get_postgres_store, create_admin_pool
from core.redis import AsyncRedisPool, SyncRedisPool, async_health_check, sync_health_check
from src.api.routers import agent, files_admin, vector_admin

from fastapi import Depends
from api.rate_limit import check_rate_limit

warnings.filterwarnings("ignore", category=LangChainBetaWarning)
logger = logging.getLogger("uvicorn")


def custom_generate_unique_id(route: APIRoute) -> str:
    return route.name


@asynccontextmanager
async def lifespan(app: FastAPI):
    """资源预热：JWKS 公钥、Redis 双池、数据库连接、Agent 插件"""
    get_jwks_client()

    await AsyncRedisPool.initialize()
    SyncRedisPool.initialize()

    try:
        async with (
            get_postgres_saver() as saver,
            get_postgres_store() as store,
            create_admin_pool() as admin_pool,
        ):
            for a in get_all_agent_info():
                try:
                    await load_agent(a.key)
                    loaded_agent = get_agent(a.key)
                    loaded_agent.checkpointer = saver
                    loaded_agent.store = store
                    logger.info("Agent %s 已成功挂载记忆体", a.key)
                except Exception as e:
                    logger.error("Failed to load agent %s: %s", a.key, e)

            app.state.admin_pool = admin_pool
            yield

    except Exception as e:
        logger.error("Error during initialization: %s", e)
        raise

    finally:
        await AsyncRedisPool.close()
        SyncRedisPool.close()


# ==============================================================================
# 1. 实例化
# ==============================================================================
app = FastAPI(lifespan=lifespan, generate_unique_id_function=custom_generate_unique_id)


# ==============================================================================
# 2. 中间件
# ==============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# 3. 健康检查（公开，无需鉴权）
#
# 设计原则：
#   - 核心依赖（postgres / redis）任一失败 → HTTP 503，让编排层摘流量
#   - 非核心依赖（langfuse）失败 → 只记录在 body，整体仍返回 200
#   - 每项检查都有独立 try/except，一项超时不阻塞其他项
# ==============================================================================
@app.get("/health", tags=["System"])
async def health_check():
    health_status: dict = {"status": "ok"}
    has_critical_failure = False

    # ── Redis ──────────────────────────────────────────────────────────────
    try:
        redis_ok = await async_health_check()
        health_status["redis"] = "connected" if redis_ok else "disconnected"
        if not redis_ok:
            has_critical_failure = True
    except Exception as e:
        logger.error("Health check: Redis error: %s", e)
        health_status["redis"] = "disconnected"
        has_critical_failure = True

    # ── PostgreSQL ─────────────────────────────────────────────────────────
    try:
        async with create_admin_pool() as pool:
            async with pool.connection() as conn:
                await conn.execute("SELECT 1")
        health_status["postgres"] = "connected"
    except Exception as e:
        logger.error("Health check: PostgreSQL error: %s", e)
        health_status["postgres"] = "disconnected"
        has_critical_failure = True

    # ── Langfuse（非核心，不影响整体状态）────────────────────────────────
    if settings.LANGFUSE_TRACING:
        try:
            health_status["langfuse"] = (
                "connected" if Langfuse().auth_check() else "disconnected"
            )
        except Exception:
            health_status["langfuse"] = "disconnected"

    # ── 核心依赖失败时返回 503 ─────────────────────────────────────────────
    if has_critical_failure:
        health_status["status"] = "degraded"
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content=health_status)

    return health_status


# ==============================================================================
# 4. 路由注册
# ==============================================================================
global_dependencies = [Depends(check_rate_limit)]

app.include_router(agent.router, dependencies=global_dependencies)
app.include_router(vector_admin.router, dependencies=global_dependencies)
app.include_router(files_admin.router, dependencies=global_dependencies)