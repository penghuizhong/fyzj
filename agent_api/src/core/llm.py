import logging
import threading
from typing import Optional

from langchain_openai import ChatOpenAI

from core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 内部单例注册表
# ---------------------------------------------------------------------------
_registry: dict[str, ChatOpenAI] = {}
_lock = threading.Lock()


# ---------------------------------------------------------------------------
# 私有：构建单个模型实例（不含缓存逻辑，便于单独测试）
# ---------------------------------------------------------------------------
def _build_model(model_name: str) -> ChatOpenAI:
    """
    根据 model_name 查找供应商配置，构造并返回 ChatOpenAI 实例。
    调用方负责缓存；本函数每次都会新建实例。
    """
    # 1. 在供应商映射表中查找
    target_provider: Optional[str] = None
    target_url: Optional[str] = None

    for p_name, p_info in settings.PROVIDER_CONFIG.items():
        if model_name in p_info.get("models", []):
            target_provider = p_name
            target_url = p_info.get("base_url")
            break

    if not target_provider or not target_url:
        logger.error("未在 config.yaml 中找到模型 %s 的配置", model_name)
        raise ValueError(f"Unsupported model: {model_name}")

    # 2. 动态获取对应的 API Key
    api_key_attr = f"{target_provider.upper()}_API_KEY"
    api_key: Optional[str] = getattr(settings, api_key_attr, None)

    if not api_key:
        raise ValueError(f"未配置环境变量: {api_key_attr}")

    # 3. 针对 DeepSeek 系列的特殊处理
    extra_body: Optional[dict] = None
    if "deepseek" in model_name.lower():
        # 强制关闭思考模式：防止 LangGraph 工具调用时丢失 reasoning_content 导致 400 报错。
        # 官方要求 extra_body 中 thinking 对象必须包含 type 字段。
        extra_body = {"thinking": {"type": "disabled"}}
        logger.info("💡 检测到 DeepSeek 模型 (%s)，已注入 extra_body 强制关闭思考模式。", model_name)

    logger.info("🤖 初始化 LLM 实例: %s (provider=%s)", model_name, target_provider)

    # 4. 构造统一的 ChatOpenAI 实例
    return ChatOpenAI(
        model=model_name,
        base_url=target_url,
        api_key=api_key,
        streaming=True,
        temperature=0.0,   # 工具调用场景，0.0 最稳定
        extra_body=extra_body,
        max_retries=3,
    )


# ---------------------------------------------------------------------------
# 公共接口
# ---------------------------------------------------------------------------
def get_model(model_name: Optional[str] = None) -> ChatOpenAI:
    """
    返回指定模型的 ChatOpenAI 单例。

    - 首次调用时构造实例并缓存，后续调用直接返回缓存。
    - 线程安全：使用双重检查锁（DCL），仅在实例缺失时竞争锁。
    - 支持运行时热替换：调用 invalidate_model() 可强制重建。
    """
    resolved = model_name or settings.DEFAULT_MODEL

    # 快速路径：绝大多数调用在此直接返回，无锁开销
    instance = _registry.get(resolved)
    if instance is not None:
        return instance

    # 慢速路径：首次创建，进锁
    with _lock:
        # 二次检查，防止多线程同时通过快速路径后重复创建
        instance = _registry.get(resolved)
        if instance is None:
            instance = _build_model(resolved)
            _registry[resolved] = instance

    return instance


def invalidate_model(model_name: Optional[str] = None) -> None:
    """
    从注册表中移除指定模型的缓存实例，下次 get_model() 时重新构造。
    适用场景：API Key 轮换、配置热更新。
    传入 None 则清空全部缓存。
    """
    with _lock:
        if model_name is None:
            cleared = list(_registry.keys())
            _registry.clear()
            logger.info("🗑️ 已清空全部模型实例缓存: %s", cleared)
        else:
            resolved = model_name or settings.DEFAULT_MODEL
            if resolved in _registry:
                del _registry[resolved]
                logger.info("🗑️ 已移除模型实例缓存: %s", resolved)