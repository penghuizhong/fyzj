
import os
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex, Settings
from llama_index.core.readers.base import BaseReader
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.readers.file import UnstructuredReader

load_dotenv()

# ── ✨ 核心改动 2：去掉 async，变成普通函数 ──
def ingest_with_llama_index(file_dir: str):
    """
    使用 LlamaIndex 进行高精度入库 (纯净同步解耦版)
    """
    
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    embedding_model = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-v3")
    
    pg_host = os.getenv("POSTGRES_HOST", "postgres")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "fyzb")
    pg_user = os.getenv("POSTGRES_USER", "postgres")
    pg_password = os.getenv("POSTGRES_PASSWORD")
    table_prefix = os.getenv("TABLE_NAME_PREFIX", "agent_server_")

    if not dashscope_api_key or not embedding_model:
        raise ValueError("DASHSCOPE_API_KEY 或 EMBEDDING_MODEL_NAME 未配置")
    
    # 1. 初始化千问 Embedding
    embed_model = DashScopeEmbedding(
        model_name=embedding_model,
        api_key=dashscope_api_key
    )
    Settings.embed_model = embed_model

    # 2. 配置解析器
    unstructured_reader = UnstructuredReader()
    supported_extensions = [".pdf", ".docx", ".doc", ".md", ".txt", ".html"]
    extension_mapping: dict[str, BaseReader] = {
        ext: unstructured_reader for ext in supported_extensions
    }

    # 3. 加载文档
    reader = SimpleDirectoryReader(
        input_dir=file_dir,
        recursive=True,
        file_extractor=extension_mapping
    )

    print(f"正在扫描并解析目录: {file_dir}...")
    documents = reader.load_data()

    if not pg_password:
        raise ValueError("POSTGRES_PASSWORD 未配置")

    # 4. 初始化 Postgres 向量存储 (同步模式)
    # 💥 关键点：LlamaIndex 会根据连接字符串自动选择驱动
    # 咱们现在强制使用 psycopg 驱动
    vector_store = PGVectorStore.from_params(
        host=pg_host,
        port=pg_port,
        database=pg_db,
        user=pg_user,
        password=pg_password,
        table_name=table_prefix,
        embed_dim=1024,  # 千问 v3 固定维度
        # 💡 使用同步驱动协议
        connection_string=f"postgresql+psycopg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
    )

    # 5. 构建索引并入库
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    print("正在计算向量并写入数据库 (同步模式)...")
    # 这里是纯同步执行，Streamlit 的进度条会一直转直到这行跑完
    VectorStoreIndex.from_documents(
        documents, 
        storage_context=storage_context,
        show_progress=True
    )
    
    print(f"🎉 入库成功！共处理 {len(documents)} 个文档对象。")