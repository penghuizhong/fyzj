import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from celery.result import AsyncResult
import asyncpg

from core.postgres import get_postgres_connection_string
from tasks.agent_tasks import ingest_knowledge_base_task
from core.config import settings # 假设您的 verify_bearer 依赖配置

logger = logging.getLogger(__name__)

# 建立专属 Router
router = APIRouter(prefix="/api/admin", tags=["Admin (向量库与任务)"])

class IngestRequest(BaseModel):
    directory_path: str

@router.post("/ingest")
async def trigger_ingestion(request: IngestRequest):
    """接收入库请求，投递至 Celery"""
    try:
        task = ingest_knowledge_base_task.delay(request.directory_path)
        return {"task_id": task.id, "status": "pending", "message": "任务已提交后台队列"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task_status/{task_id}")
async def get_task_status(task_id: str):
    """供前台轮询任务进度"""
    try:
        task_result = AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result if task_result.ready() else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tables")
async def get_vector_tables():
    """获取所有向量表"""
    try:
        conn_str = get_postgres_connection_string().replace("postgresql://", "postgresql+asyncpg://")
        conn = await asyncpg.connect(conn_str)
        try:
            records = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'data_%'")
            return {"tables": [r["tablename"] for r in records]}
        finally:
            await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chunks")
async def get_chunks(table_name: str, search: str = "", limit: int = 10, offset: int = 0):
    """供切片浏览器调用的数据接口"""
    try:
        safe_table = table_name.replace('"', '').replace(';', '')
        if not safe_table.startswith("data_"):
            raise HTTPException(status_code=400, detail="Invalid table name")

        conn_str = get_postgres_connection_string().replace("postgresql://", "postgresql+asyncpg://")
        conn = await asyncpg.connect(conn_str)
        
        try:
            total = await conn.fetchval(f'SELECT COUNT(*) FROM "{safe_table}"') or 0
            avg_len = await conn.fetchval(f'SELECT AVG(LENGTH(text)) FROM "{safe_table}"') or 0
            max_len = await conn.fetchval(f'SELECT MAX(LENGTH(text)) FROM "{safe_table}"') or 0
            
            if search:
                count_query = f'SELECT COUNT(*) FROM "{safe_table}" WHERE text ILIKE $1'
                total_filtered = await conn.fetchval(count_query, f"%{search}%") or 0
                rows = await conn.fetch(f'SELECT id, text, metadata_ FROM "{safe_table}" WHERE text ILIKE $1 ORDER BY id ASC LIMIT $2 OFFSET $3', f"%{search}%", limit, offset)
            else:
                total_filtered = total
                rows = await conn.fetch(f'SELECT id, text, metadata_ FROM "{safe_table}" ORDER BY id ASC LIMIT $1 OFFSET $2', limit, offset)

            chunks = []
            for r in rows:
                meta = r.get("metadata_") or "{}"
                import json
                if isinstance(meta, str): meta = json.loads(meta)
                txt = r.get("text", "")
                chunks.append({
                    "id": str(r.get("id")),
                    "text": txt,
                    "token_est": max(1, len(txt) // 2),
                    "char_len": len(txt),
                    "source": meta.get("file_name") or "未知",
                    "page": meta.get("page_label") or "—"
                })

            return {
                "chunks": chunks, 
                "total_filtered": int(total_filtered),
                "stats": {"total": int(total), "avg_tok": max(1, int(avg_len)//2), "max_tok": max(1, int(max_len)//2)}
            }
        finally:
            await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))