"""
方圆智版 · 向量库后台管理 API (admin.py)
实现知识库的完整 CRUD (增删改查) 与异步任务调度
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from celery.result import AsyncResult
import asyncpg

from core.postgres import get_postgres_connection_string
from tasks.agent_tasks import ingest_knowledge_base_task

logger = logging.getLogger(__name__)

# 建立专属 Router
router = APIRouter(prefix="/api/vector-admin", tags=["Admin (向量库与任务)"])

# =====================================================================
# 🛠️ 辅助函数：确保异步数据库连接字符串正确
# =====================================================================
def get_async_pg_url() -> str:
    """确保使用 asyncpg 驱动进行异步数据库操作"""
    conn_str = get_postgres_connection_string()
  
    return conn_str


# =====================================================================
# 📚 数据模型定义
# =====================================================================
class IngestRequest(BaseModel):
    directory_path: str

class DeleteDocumentRequest(BaseModel):
    table_name: str
    file_name: str


# =====================================================================
# 🟢 增 (CREATE) / 改 (UPDATE) - 异步入库
# =====================================================================
@router.post("/ingest")
async def trigger_ingestion(request: IngestRequest):
    """
    【增/改】接收入库请求，投递至 Celery
    注意：在 LlamaIndex 配合正确 docstore 的情况下，针对同一目录的重复调用将触发 Upsert(增量更新)
    """
    try:
        task = ingest_knowledge_base_task.delay(request.directory_path)
        logger.info(f"入库任务已投递，路径: {request.directory_path}, Task ID: {task.id}")
        return {"task_id": task.id, "status": "pending", "message": "任务已提交后台队列"}
    except Exception as e:
        logger.error(f"任务投递失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task_status/{task_id}")
async def get_task_status(task_id: str):
    """供前台轮询入库任务进度"""
    try:
        task_result = AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result if task_result.ready() else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# 🔴 删 (DELETE) - 物理清理向量表中的特定文档
# =====================================================================
@router.delete("/document")
async def delete_document(request: DeleteDocumentRequest):
    """
    【删】根据文件名，物理删除特定向量表中的所有相关切片。
    当本地文件被删除或需要强制覆盖更新时调用。
    """
    safe_table = request.table_name.replace('"', "").replace(";", "")
    if not safe_table.startswith("data_"):
        raise HTTPException(status_code=400, detail="Invalid table name")

    if not request.file_name:
        raise HTTPException(status_code=400, detail="file_name cannot be empty")

    try:
        conn = await asyncpg.connect(get_async_pg_url())
        try:
            # 根据 metadata 中的 file_name 字段精准狙击并删除该文档的所有 Chunk
            delete_sql = f"""
                DELETE FROM "{safe_table}" 
                WHERE metadata_->>'file_name' = $1
            """
            result = await conn.execute(delete_sql, request.file_name)
            
            # execute 返回的 result 格式类似 "DELETE 15" (删除了15条切片)
            deleted_count = int(result.split(" ")[1]) if result.startswith("DELETE") else 0
            
            logger.info(f"已从表 {safe_table} 中删除文件 {request.file_name} 的 {deleted_count} 条切片。")
            return {
                "status": "success", 
                "message": f"成功删除 {deleted_count} 条关联切片",
                "deleted_chunks": deleted_count
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"删除文档切片失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# 🔵 查 (READ) - 获取表与切片数据
# =====================================================================
@router.get("/tables")
async def get_vector_tables():
    """【查】获取所有向量表"""
    try:
        conn = await asyncpg.connect(get_async_pg_url())
        try:
            records = await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'data_%'"
            )
            return {"tables": [r["tablename"] for r in records]}
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"获取向量表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunks")
async def get_chunks(table_name: str, search: str = "", limit: int = 10, offset: int = 0):
    """【查】供切片浏览器调用的数据接口，支持分页与关键词检索"""
    safe_table = table_name.replace('"', "").replace(";", "")
    if not safe_table.startswith("data_"):
        raise HTTPException(status_code=400, detail="Invalid table name")

    try:
        conn = await asyncpg.connect(get_async_pg_url())
        try:
            total = await conn.fetchval(f'SELECT COUNT(*) FROM "{safe_table}"') or 0
            avg_len = await conn.fetchval(f'SELECT AVG(LENGTH(text)) FROM "{safe_table}"') or 0
            max_len = await conn.fetchval(f'SELECT MAX(LENGTH(text)) FROM "{safe_table}"') or 0

            if search:
                count_query = f'SELECT COUNT(*) FROM "{safe_table}" WHERE text ILIKE $1'
                total_filtered = await conn.fetchval(count_query, f"%{search}%") or 0
                rows = await conn.fetch(
                    f'SELECT id, text, metadata_ FROM "{safe_table}" WHERE text ILIKE $1 ORDER BY id ASC LIMIT $2 OFFSET $3',
                    f"%{search}%",
                    limit,
                    offset,
                )
            else:
                total_filtered = total
                rows = await conn.fetch(
                    f'SELECT id, text, metadata_ FROM "{safe_table}" ORDER BY id ASC LIMIT $1 OFFSET $2',
                    limit,
                    offset,
                )

            chunks = []
            import json
            for r in rows:
                meta = r.get("metadata_") or "{}"
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except:
                        meta = {}
                txt = r.get("text", "")
                chunks.append(
                    {
                        "id": str(r.get("id")),
                        "text": txt,
                        "token_est": max(1, len(txt) // 2),
                        "char_len": len(txt),
                        "source": meta.get("file_name") or "未知",
                        "page": meta.get("page_label") or "—",
                    }
                )

            return {
                "chunks": chunks,
                "total_filtered": int(total_filtered),
                "stats": {
                    "total": int(total),
                    "avg_tok": max(1, int(avg_len) // 2),
                    "max_tok": max(1, int(max_len) // 2),
                },
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"获取切片数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))