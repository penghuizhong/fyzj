import logging
from pathlib import Path
from typing import Any

import yaml
from dotenv import find_dotenv
from pydantic import (
    Field,
    SecretStr,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("uvicorn")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_dotenv(),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # ==========================================
    # 1. 基础网络配置
    # ==========================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    MODE: str = "production"
    GRACEFUL_SHUTDOWN_TIMEOUT: int = 30

    # ==========================================
    # 2. 核心大模型配置 (Agent 专属)
    # ==========================================
    DEEPSEEK_API_KEY: SecretStr | None = None
    DASHSCOPE_API_KEY: SecretStr | None = None
    OPENAI_API_KEY: SecretStr | None = None
    ENABLE_SAFEGUARD: bool = True
    LANGFUSE_TRACING: bool = False
    
    # 动态加载的配置项
    DEFAULT_MODEL: str = "deepseek-chat"
    AVAILABLE_MODELS: list[str] = []
    PROVIDER_CONFIG: dict[str, dict] = {}

    # ==========================================
    # 3. 基础设施：PostgreSQL (LangGraph Checkpointer)
    # ==========================================
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: SecretStr | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_APPLICATION_NAME: str = "agent_service"
    TABLE_NAME_PREFIX: str = "agent_server_"
    
    # psycopg_pool 原生连接池优化 (非 SQLAlchemy)
    POSTGRES_POOL_OPEN_TIMEOUT: int = 30
    POSTGRES_POOL_CLOSE_TIMEOUT: int = 10
    POSTGRES_POOL_MAX_IDLE_TIME: int = 300
    POSTGRES_MIN_CONNECTIONS_PER_POOL: int = 1
    POSTGRES_MAX_CONNECTIONS_PER_POOL: int = 3

    # ==========================================
    # 4. 基础设施：Redis 与 Celery
    # ==========================================
    REDIS_URL: str = "redis://localhost:6379/1"
    REDIS_MAX_CONNECTIONS: int = 50
    
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_WORKER_CONCURRENCY: int = 4

    # ==========================================
    # 5. 安全防护与鉴权 (验证机模式)
    # ==========================================
    # Agent 只验证，不签发。使用公钥进行 RS256 解密（或者共享 Secret）
    JWT_PUBLIC_KEY: SecretStr | None = None
    JWT_ALGORITHM: str = "RS256"
    
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_ANONYMOUS: str = "5/minute"
    RATE_LIMIT_AUTHENTICATED: str = "50/minute"


    def model_post_init(self, __context: Any) -> None:
        """初始化后自动读取项目根目录下的 config.yaml (用于管理 LLM 提供商)"""
        current_file = Path(__file__).resolve()

        possible_roots = [
            current_file.parent.parent.parent,
            current_file.parent.parent,
        ]

        yaml_path = None
        for root in possible_roots:
            candidate = root / "config.yaml"
            if candidate.exists():
                yaml_path = candidate
                break

        if yaml_path is None:
            yaml_path = current_file.parent.parent.parent / "config.yaml"

        if yaml_path.exists():
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    self.PROVIDER_CONFIG = data.get("providers", {})

                    models = []
                    for p_val in self.PROVIDER_CONFIG.values():
                        models.extend(p_val.get("models", []))
                    self.AVAILABLE_MODELS = models

                    self.DEFAULT_MODEL = data.get("default_model", self.DEFAULT_MODEL)
                logger.info(f"✅ 成功从 {yaml_path} 加载大模型配置")
            except Exception as e:
                logger.error(f"❌ 加载 config.yaml 失败: {e}")
        else:
            logger.warning(f"⚠️ 未找到 {yaml_path}, 将使用系统默认模型")

    @computed_field
    @property
    def BASE_URL(self) -> str:
        return f"http://{self.HOST}:{self.PORT}"

    def is_dev(self) -> bool:
        return self.MODE.lower() == "dev"

settings = Settings()