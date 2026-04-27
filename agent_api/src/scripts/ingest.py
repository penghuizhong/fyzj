"""
方圆智版 · 后台异步入库引擎 (Celery 专用)
包含：MD5真·增量更新、动态分类打标、PGVector 物理清理、空数据清洗与并发限流
文件路径: agent_api/src/scripts/ingest.py
"""

import logging
import hashlib
import time
import os
from sqlalchemy import create_engine, text
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex, Settings
from llama_index.core.readers.base import BaseReader
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.readers.file import UnstructuredReader

from core.config import settings

logger = logging.getLogger(__name__)

def get_file_md5(file_path: str) -> str:
    """计算物理文件的 MD5 哈希指纹"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"无法计算文件哈希 {file_path}: {e}")
        return ""

def ingest_with_llama_index(file_dir: str) -> int:
    """
    后台异步高精度入库 (MD5 哈希指纹增量 + 自动打标版 + 脏数据过滤)
    
    Returns:
        int: 成功进行向量化的 Document/Chunk 数量
    """
    logger.info(f"开始扫描并解析目录: {file_dir}")
    
    if not settings.POSTGRES_PASSWORD:
        raise ValueError("POSTGRES_PASSWORD 未配置")
    db_password = settings.POSTGRES_PASSWORD.get_secret_value()
    dashscope_key = settings.DASHSCOPE_API_KEY.get_secret_value()
    embedding_model = getattr(settings, "EMBEDDING_MODEL_NAME", "text-embedding-v3")

    # 1. 初始化千问 Embedding (带 10 并发防爆限流)
    embed_model = DashScopeEmbedding(
        model_name=embedding_model, 
        api_key=dashscope_key,
        embed_batch_size=10  # 🌟 核心防线 1：每次最多只发10个切片给阿里，防止超载丢包
    )
    Settings.embed_model = embed_model

    # 2. 配置高精度文档解析器
    try:
        unstructured_reader = UnstructuredReader()
        supported_extensions = [".pdf", ".docx", ".doc", ".md", ".txt", ".html"]
        extension_mapping: dict[str, BaseReader] = {ext: unstructured_reader for ext in supported_extensions}
    except ImportError:
        logger.warning("未检测到 Unstructured 依赖，将降级使用原生解析器")
        extension_mapping = None

    # 3. 加载目录中的所有文档对象
    try:
        reader = SimpleDirectoryReader(input_dir=file_dir, recursive=True, file_extractor=extension_mapping)
        documents = reader.load_data()
    except Exception as e:
        logger.error(f"读取目录 {file_dir} 失败: {e}")
        raise e

    if not documents:
        logger.warning(f"目录 {file_dir} 中未找到任何支持的文档")
        return 0

    # =========================================================================
    # 🌟 核心中枢 1：Metadata 强力注入流水线 (洗数据、打标签、算哈希)
    # =========================================================================
    file_hashes = {}
    current_timestamp = int(time.time())

    for doc in documents:
        fpath = doc.metadata.get("file_path", "")
        fname = doc.metadata.get("file_name", "未知文件.txt")

        # 动态路由分类 (Category) - 供 tools.py 精准检索使用
        category = "通用" # 默认兜底分类
        fpath_lower = fpath.lower()
        
        # 遍历 settings 中加载的 yaml 规则
        for target_category, keywords in settings.CATEGORY_RULES.items():
            if any(kw in fpath_lower for kw in keywords):
                category = target_category
                break

        # 计算 MD5 指纹
        if fpath and fpath not in file_hashes:
            file_hashes[fpath] = get_file_md5(fpath)
        fhash = file_hashes.get(fpath, "")

        # 强制覆写注入 Metadata
        doc.metadata["category"] = category
        doc.metadata["file_hash"] = fhash
        doc.metadata["timestamp"] = current_timestamp
        doc.metadata["file_name"] = fname 

        # 剔除冗余标签，保持数据库纯净
        doc.metadata.pop("file_path", None)
        doc.metadata.pop("creation_date", None)
        doc.metadata.pop("last_modified_date", None)

    # =========================================================================
    # 🌟 核心中枢 2：连接数据库查重，提取历史哈希
    # =========================================================================
    sync_connection_string = (
        f"postgresql+psycopg://{settings.POSTGRES_USER}:{db_password}@"
        f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    engine = create_engine(sync_connection_string)
    safe_table = settings.TABLE_NAME_PREFIX.replace('"', '').replace(';', '')
    table_name = f"data_{safe_table}"

    existing_files = {}
    try:
        with engine.connect() as conn:
            query = text(f"""
                SELECT metadata_->>'file_name', MAX(metadata_->>'file_hash') 
                FROM "{table_name}" 
                GROUP BY metadata_->>'file_name'
            """)
            res = conn.execute(query)
            for row in res:
                existing_files[row[0]] = row[1]
    except Exception as e:
        logger.warning(f"无法获取历史哈希 (首次建库或表不存在正常跳过): {e}")

    # =========================================================================
    # 🌟 核心中枢 3：哈希比对与增量筛选
    # =========================================================================
    docs_to_process = []
    files_to_delete = set()
    skipped_files = set()
    processed_files = set()

    for doc in documents:
        fname = doc.metadata.get("file_name")
        fhash = doc.metadata.get("file_hash")

        if fname in existing_files:
            if existing_files[fname] == fhash:
                # 哈希一致 -> 跳过
                skipped_files.add(fname)
                continue
            else:
                # 哈希改变 -> 标记删除旧数据，准备入库新数据
                files_to_delete.add(fname)
                docs_to_process.append(doc)
                processed_files.add(fname)
        else:
            # 纯新文件 -> 准备入库
            docs_to_process.append(doc)
            processed_files.add(fname)

    logger.info(f"🔎 扫描完毕。跳过未变动文件: {len(skipped_files)} 个。发现新增/修改: {len(processed_files)} 个。")

    if not docs_to_process:
        logger.info("✅ 所有文件均无变动，无需耗费 Token，安全退出。")
        return 0

    # =========================================================================
    # 🌟 核心防线 2：物理清洗空数据 (防止 Pydantic ValidationError 崩溃)
    # =========================================================================
    clean_docs = []
    for doc in docs_to_process:
        # 确保切片内含有实质性文本，剔除纯图片页或幽灵空白符
        if doc.text and doc.text.strip():
            clean_docs.append(doc)
        else:
            logger.warning(f"⚠️ 拦截到空切片，已丢弃 (来源: {doc.metadata.get('file_name', '未知')})")

    if not clean_docs:
        logger.warning("🚫 提取后发现所有内容全为空(可能是纯图片PDF或无文本格式)，操作中止。")
        return 0

    # =========================================================================
    # 🌟 核心中枢 4：物理删除脏数据 & 全新向量化落盘
    # =========================================================================
    if files_to_delete:
        try:
            with engine.begin() as conn:
                for fname in files_to_delete:
                    delete_query = text(f'DELETE FROM "{table_name}" WHERE metadata_->>\'file_name\' = :fname')
                    conn.execute(delete_query, {"fname": fname})
                    logger.info(f"🧹 已彻底抹除被修改文件 [{fname}] 的旧版切片。")
        except Exception as e:
            logger.error(f"清理旧切片失败: {e}")

    # 开始最终的 DashScope 向量化
    vector_store = PGVectorStore.from_params(
        host=settings.POSTGRES_HOST,
        port=str(settings.POSTGRES_PORT),
        database=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=db_password,
        table_name=settings.TABLE_NAME_PREFIX,
        embed_dim=1024,
        connection_string=sync_connection_string
    )

    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    logger.info(f"🚀 调用千问 API 进行向量化 (本次处理 {len(clean_docs)} 个有效切片)...")
    VectorStoreIndex.from_documents(
        clean_docs, 
        storage_context=storage_context,
        show_progress=False 
    )
    
    logger.info("🎉 方圆智版入库引擎：增量作业完美收官！")
    return len(clean_docs)