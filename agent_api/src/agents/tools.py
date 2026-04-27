import logging
from typing import Optional
from langchain_core.tools import tool
from rapidfuzz import process, fuzz  # 引入轻量级模糊匹配库

# LlamaIndex 原装组件
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.dashscope import DashScopeEmbedding
# 🌟 新增：引入 LlamaIndex 的元数据过滤器
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters 

from src.core import settings

logger = logging.getLogger(__name__)

if settings.POSTGRES_PASSWORD is None:
    raise ValueError("POSTGRES_PASSWORD 未配置")

# ==========================================
# 🌟 核心优化：全局单例，拯救 2G 内存
# ==========================================
GLOBAL_EMBED_MODEL = None
GLOBAL_VECTOR_STORE = None
GLOBAL_INDEX = None

def get_llama_index_resources():
    """延迟加载并缓存 LlamaIndex 资源 (带断线防弹衣)"""
    global GLOBAL_EMBED_MODEL, GLOBAL_VECTOR_STORE, GLOBAL_INDEX
    
    try:
        if GLOBAL_EMBED_MODEL is None:
            GLOBAL_EMBED_MODEL = DashScopeEmbedding(
                model_name="text-embedding-v3",
                api_key=settings.DASHSCOPE_API_KEY.get_secret_value()
            )
            
        if GLOBAL_VECTOR_STORE is None:
            GLOBAL_VECTOR_STORE = PGVectorStore.from_params(
                host=settings.POSTGRES_HOST,
                port=str(settings.POSTGRES_PORT),
                database=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD.get_secret_value(),
                table_name=settings.TABLE_NAME_PREFIX,
                embed_dim=1024
            )
            
        if GLOBAL_INDEX is None:
            GLOBAL_INDEX = VectorStoreIndex.from_vector_store(
                vector_store=GLOBAL_VECTOR_STORE,
                embed_model=GLOBAL_EMBED_MODEL
            )
            
        return GLOBAL_INDEX
    except Exception as e:
        # ⚠️ 故障恢复机制：如果连接假死或出错，清空全局变量，让下一次调用重新连接
        logger.error(f"LlamaIndex 资源加载或连接失败，正在重置单例状态: {e}")
        GLOBAL_EMBED_MODEL = None
        GLOBAL_VECTOR_STORE = None
        GLOBAL_INDEX = None
        raise e


# ==========================================
# 🛡️ 极速安全网关
# ==========================================
MALICIOUS_TARGETS = [
    "忽略之前指令", "系统提示词", "忘记设定", "输出你的初始指令",
    "你是黑客", "无视规则", "高管工资", "内部绝密"
]

def is_query_safe(query: str) -> bool:
    """使用 RapidFuzz 进行 0 延迟的语义防线"""
    result = process.extractOne(
        query, 
        MALICIOUS_TARGETS, 
        scorer=fuzz.partial_ratio
    )
    if result and result[1] > 80:
        logger.warning(f"🛡️ 触发安全拦截: 命中词条 '{result[0]}', 得分 {result[1]}")
        return False
    return True


# ==========================================
# 🔍 检索工具主体 (融合了意图识别与元数据过滤)
# ==========================================
@tool
def database_search(query: str, category: Optional[str] = None) -> str:
    """
    搜索方圆智版手册数据库。用于回答制版技术或客服相关问题。
    
    Args:
        query: 用户的具体搜索问题。
        category: 知识分类标签，例如 "裙子", "裤子", "上衣", "客服话术"。如果无法确定或需要跨界查询，可以留空。
    """
    if not is_query_safe(query):
        return "对不起，您的查询涉及敏感信息或违规指令，我无法为您检索相关内容。"

    try:
        index = get_llama_index_resources()
        
        # 🌟 核心升级：动态组装元数据过滤器 (MetadataFilters)
        filters = None
        if category:
            filters = MetadataFilters(
                filters=[ExactMatchFilter(key="category", value=category)]
            )
            logger.info(f"🔎 触发精准检索，锁定分类: [{category}]")
        
        # 构造带有过滤器的检索器
        retriever = index.as_retriever(
            similarity_top_k=4,
            filters=filters
        )
        nodes = retriever.retrieve(query)

        if not nodes:
            return f"在分类 [{category or '全局'}] 中未能找到关于 '{query}' 的相关内容。"

        # 格式化输出
        formatted_results = []
        for i, node_with_score in enumerate(nodes):
            node = node_with_score.node
            
            page_num = node.metadata.get("page_label", node.metadata.get("page", "未知"))
            file_name = node.metadata.get("file_name", "员工手册")
            
            content = node.get_content().strip().replace("\n", " ")
            
            result_item = (
                f"--- 来源 [{i+1}] ({file_name} 第 {page_num} 页) ---\n"
                f"{content}"
            )
            formatted_results.append(result_item)

        return f"针对问题 '{query}'，我找到了以下参考信息：\n\n" + "\n\n".join(formatted_results)

    except Exception as e:
        logger.error(f"检索彻底失败 - Query: {query} | Category: {category} | Error: {e}", exc_info=True)
        return f"数据库查询超时或出错，请联系系统管理员。({str(e)})"