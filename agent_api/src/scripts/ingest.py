"""
方圆智版 · 后台异步入库引擎 (Celery 专用)
文件路径: agent_api/src/scripts/ingest.py
"""

import logging
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex, Settings
from llama_index.core.readers.base import BaseReader
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.readers.file import UnstructuredReader

# 🌟 核心改动 1：回归微服务正轨，统一使用全局配置
from core.config import settings

# 🌟 核心改动 2：使用标准日志器，对接 Celery 日志系统
logger = logging.getLogger(__name__)

def ingest_with_llama_index(file_dir: str) -> int:
    """
    后台异步高精度入库。
    由 Celery Worker 调用，全程阻塞执行，安全隔离。
    
    Returns:
        int: 成功入库的 Document/Chunk 数量
    """
    logger.info(f"开始扫描并解析目录: {file_dir}")
    
    # 1. 提取密码和 API Key
    if not settings.POSTGRES_PASSWORD:
        raise ValueError("POSTGRES_PASSWORD 未配置")
    db_password = settings.POSTGRES_PASSWORD.get_secret_value()
    
    if not settings.DASHSCOPE_API_KEY:
        raise ValueError("DASHSCOPE_API_KEY 未配置")
    dashscope_key = settings.DASHSCOPE_API_KEY.get_secret_value()
    
    # 从配置中获取模型名，支持降级
    embedding_model = getattr(settings, "EMBEDDING_MODEL_NAME", "text-embedding-v3")

    # 2. 初始化千问 Embedding
    embed_model = DashScopeEmbedding(
        model_name=embedding_model,
        api_key=dashscope_key
    )
    # 在独立的 Worker 进程中全局赋值是安全的
    Settings.embed_model = embed_model

    # 3. 配置高精度文档解析器 (Unstructured)
    try:
        unstructured_reader = UnstructuredReader()
        supported_extensions = [".pdf", ".docx", ".doc", ".md", ".txt", ".html"]
        extension_mapping: dict[str, BaseReader] = {
            ext: unstructured_reader for ext in supported_extensions
        }
    except ImportError:
        logger.warning("未检测到 Unstructured 依赖，将降级使用 LlamaIndex 原生解析器")
        extension_mapping = None

    # 4. 加载文档
    try:
        reader = SimpleDirectoryReader(
            input_dir=file_dir,
            recursive=True,
            file_extractor=extension_mapping
        )
        documents = reader.load_data()
    except Exception as e:
        logger.error(f"读取目录 {file_dir} 失败: {e}")
        raise e

    if not documents:
        logger.warning(f"目录 {file_dir} 中未找到任何支持的文档")
        return 0

    logger.info(f"文档解析完成，共提取 {len(documents)} 个文档对象准备进行向量化。")

    # 5. 初始化 Postgres 向量存储 (强制使用同步模式)
    # 💥 关键点：为 Celery 拼装标准的纯同步 psycopg 连接
    sync_connection_string = (
        f"postgresql+psycopg://{settings.POSTGRES_USER}:{db_password}@"
        f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )

    vector_store = PGVectorStore.from_params(
        host=settings.POSTGRES_HOST,
        port=str(settings.POSTGRES_PORT),
        database=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=db_password,
        table_name=settings.TABLE_NAME_PREFIX,
        embed_dim=1024,  # 千问 v3 固定维度
        connection_string=sync_connection_string
    )

    # 6. 构建索引并入库
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    logger.info("正在调用 DashScope 计算向量并写入 PostgreSQL 数据库 (此过程较长)...")
    
    # 🌟 核心改动 3：关闭 show_progress，防止进度条刷爆 Docker 日志文件
    VectorStoreIndex.from_documents(
        documents, 
        storage_context=storage_context,
        show_progress=False 
    )
    
    logger.info(f"🎉 入库成功！目录 {file_dir} 处理完毕。")
    return len(documents)