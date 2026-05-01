import json
import logging
from typing import Annotated, AsyncGenerator

import psycopg
from psycopg import sql  # ✅ 引入 sql 模块，处理动态表名
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel
from celery.result import AsyncResult

from tasks.agent_tasks import ingest_knowledge_base_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vector-admin", tags=["Admin (向量库与任务)"])

# ── 依赖注入 ──────────────────────────────────────────────────────────
async def get_admin_conn(request: Request) -> AsyncGenerator[psycopg.AsyncConnection, None]:
    pool: AsyncConnectionPool = request.app.state.admin_pool
    async with pool.connection() as conn:
        yield conn

# ── 数据模型 ──────────────────────────────────────────────────────────
class IngestRequest(BaseModel):
    directory_path: str

class DeleteDocumentRequest(BaseModel):
    table_name: str
    file_name: str

# ── 工具函数 ──────────────────────────────────────────────────────────
def _validate_table_name(table_name: str) -> str:
    """仅做基础校验，防注入由 psycopg.sql.Identifier 负责"""
    if not table_name.startswith("data_"):
        raise HTTPException(status_code=400, detail="Invalid table name format. Must start with 'data_'")
    return table_name

# ── 增/改：异步入库 ───────────────────────────────────────────────────
@router.post("/ingest")
async def trigger_ingestion(request: IngestRequest):
    try:
        task = ingest_knowledge_base_task.delay(request.directory_path)
        logger.info(f"入库任务已投递，路径: {request.directory_path}, Task ID: {task.id}")
        return {"task_id": task.id, "status": "pending", "message": "任务已提交后台队列"}
    except Exception as e:
        logger.error(f"任务投递失败: {e}")
        raise HTTPException(status_code=500, detail="内部任务队列错误")

@router.get("/task_status/{task_id}")
async def get_task_status(task_id: str):
    try:
        task_result = AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result if task_result.ready() else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── 删：物理清理向量切片 ───────────────────────────────────────────────
@router.delete("/document")
async def delete_document(
    request: Annotated[DeleteDocumentRequest, Body()],
    conn: psycopg.AsyncConnection = Depends(get_admin_conn),
):
    safe_table = _validate_table_name(request.table_name)
    if not request.file_name:
        raise HTTPException(status_code=400, detail="file_name cannot be empty")

    try:
        async with conn.cursor() as cur:
            # ✅ 使用 psycopg.sql 构建安全查询
            query = sql.SQL("DELETE FROM {} WHERE metadata_->>%s = %s").format(
                sql.Identifier(safe_table)
            )
            await cur.execute(query, ("file_name", request.file_name))
            deleted_count = cur.rowcount
            
        logger.info(f"已从表 {safe_table} 删除文件 {request.file_name} 的 {deleted_count} 条切片")
        return {
            "status": "success",
            "message": f"成功删除 {deleted_count} 条关联切片",
            "deleted_chunks": deleted_count,
        }
    except Exception as e:
        logger.error(f"删除文档切片失败: {e}")
        raise HTTPException(status_code=500, detail="数据库删除操作失败")

# ── 查：获取所有向量表 ─────────────────────────────────────────────────
@router.get("/tables")
async def get_vector_tables(
    conn: psycopg.AsyncConnection = Depends(get_admin_conn),
):
    try:
        async with conn.cursor() as cur:
            # 基础系统表查询，不需要动态拼接，直接用普通字串即可
            await cur.execute(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname='public' AND tablename LIKE 'data_%'"
            )
            rows = await cur.fetchall()
        # default fetchall() returns list of tuples: [('data_1',), ('data_2',)]
        return {"tables": [r[0] for r in rows]} 
    except Exception as e:
        logger.error(f"获取向量表失败: {e}")
        raise HTTPException(status_code=500, detail="获取表列表失败")

# ── 查：切片浏览器（分页 + 关键词检索）────────────────────────────────
@router.get("/chunks")
async def get_chunks(
    table_name: str,
    search: str = "",
    limit: int = 10,
    offset: int = 0,
    conn: psycopg.AsyncConnection = Depends(get_admin_conn),
):
    safe_table = _validate_table_name(table_name)

    try:
        async with conn.cursor(row_factory=dict_row) as cur:
            # ✅ 优化 1：合并总数与统计信息的查询，减少一次 DB round-trip
            stat_query = sql.SQL(
                "SELECT COUNT(*) AS n, AVG(LENGTH(text)) AS a, MAX(LENGTH(text)) AS m FROM {}"
            ).format(sql.Identifier(safe_table))
            
            await cur.execute(stat_query)
            stat = await cur.fetchone()
            
            total = stat["n"] or 0
            avg_len = stat["a"] or 0
            max_len = stat["m"] or 0

            # ✅ 优化 2：根据是否有 search 进行不同逻辑，且全面使用 sql.SQL 防注入
            if search:
                count_filtered_query = sql.SQL(
                    "SELECT COUNT(*) AS n FROM {} WHERE text ILIKE %s"
                ).format(sql.Identifier(safe_table))
                await cur.execute(count_filtered_query, (f"%{search}%",))
                total_filtered = (await cur.fetchone())["n"] or 0

                fetch_query = sql.SQL(
                    "SELECT id, text, metadata_ FROM {} WHERE text ILIKE %s ORDER BY id ASC LIMIT %s OFFSET %s"
                ).format(sql.Identifier(safe_table))
                await cur.execute(fetch_query, (f"%{search}%", limit, offset))
            else:
                total_filtered = total
                fetch_query = sql.SQL(
                    "SELECT id, text, metadata_ FROM {} ORDER BY id ASC LIMIT %s OFFSET %s"
                ).format(sql.Identifier(safe_table))
                await cur.execute(fetch_query, (limit, offset))

            rows = await cur.fetchall()

        chunks = []
        for r in rows:
            meta = r.get("metadata_") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            
            txt = r.get("text", "")
            chunks.append({
                "id": str(r.get("id")),
                "text": txt,
                "token_est": max(1, len(txt) // 2),
                "char_len": len(txt),
                "source": meta.get("file_name", "未知"),
                "page": meta.get("page_label", "—"),
            })

        return {
            "chunks": chunks,
            "total_filtered": int(total_filtered),
            "stats": {
                "total": int(total),
                "avg_tok": max(1, int(avg_len) // 2),
                "max_tok": max(1, int(max_len) // 2),
            },
        }
    except psycopg.errors.UndefinedTable:
        # 专门捕获表不存在的错误，返回更友好的 404
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    except Exception as e:
        logger.error(f"获取切片数据失败: {e}")
        raise HTTPException(status_code=500, detail="读取切片数据异常")