"""
Application configuration loaded from environment variables.

Uses pydantic-settings for type-safe configuration management.
All sensitive values should be provided via environment variables or .env file.
"""

from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import json

# Resolve .env relative to this file: backend/app/core/config.py
# -> .env is at backend/.env
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file= ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    PROJECT_NAME: str = "E-Commerce-Customer-Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "mysql+aiomysql://root:111111@localhost:13306/customer_service"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_RECYCLE: int = 3600

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None

    # LLM Provider (openai / anthropic / local)
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4-turbo-preview"
    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_MAX_TOKENS: int = 2000
    LLM_TEMPERATURE: float = 0.7

    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"

    # Local LLM
    LOCAL_LLM_API_BASE: str = "http://localhost:8000/v1"
    LOCAL_LLM_MODEL: str = "Qwen/Qwen2-72B-Instruct"

    # Embedding Provider
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSION: int = 1536

    # Vector Store
    VECTOR_STORE_TYPE: str = "milvus"
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "knowledge_base"

    # JWT Authentication
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"] # "http://localhost:3000", "http://localhost:80"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> List[str]:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return [origin.strip() for origin in value.split(",")]
        if isinstance(value, list):
            return value
        return ["http://localhost:3000"]

    # File Storage (MinIO)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "chat-attachments"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_MAX_REQUESTS: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @property
    def is_llm_configured(self) -> bool:
        """Check if LLM provider has an API key configured."""
        if self.LLM_PROVIDER == "anthropic":
            return bool(self.ANTHROPIC_API_KEY)
        if self.LLM_PROVIDER == "local":
            return bool(self.LOCAL_LLM_API_BASE)
        return bool(self.LLM_API_KEY)


# Global settings instance
settings = Settings()