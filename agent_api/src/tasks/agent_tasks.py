"""Celery tasks for background processing (ETL & Ingestion)."""

import logging
from celery import shared_task

# 假设您的原始入库脚本在 scripts.ingest 中
from scripts.ingest import ingest_with_llama_index

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="ingest_knowledge_base_task")
def ingest_knowledge_base_task(self, directory_path: str) -> dict:
    """
    后台异步入库任务：接收路径，执行向量化与写入数据库。
    所有的耗时操作都在这个独立进程中完成，绝对不阻塞 API。
    """
    logger.info(f"🚀 Celery Worker 领到任务，开始异步入库，目标路径: {directory_path}")
    try:
        # 纯同步调用，因为 Celery worker 本身就是用来跑阻塞任务的
        ingest_with_llama_index(directory_path)

        logger.info(f"✅ 目录 {directory_path} 知识库入库成功")
        return {"status": "success", "message": f"Successfully ingested {directory_path}"}
        
    except Exception as exc:
        logger.error(f"❌ 入库任务彻底失败: {str(exc)}", exc_info=True)
        # 抛出异常，Celery 会自动将此任务的状态标记为 FAILURE
        raise exc