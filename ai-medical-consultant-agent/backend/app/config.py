# ============================================================
# AI Medical Consultant - Configuration
# ============================================================
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # --- LLM Configuration ---
    LLM_API_KEY: str = "your-deepseek-api-key"
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-chat"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096

    # --- Embedding ---
    EMBEDDING_API_KEY: str = "your-embedding-api-key"
    EMBEDDING_MODEL: str = "text-embedding-v1"

    # --- Database ---
    # 默认使用 SQLite（本地开发），生产环境使用 PostgreSQL
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/medical.db"
    DATABASE_URL_SYNC: str = "sqlite:///./data/medical.db"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- FAISS ---
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    VECTOR_DIMENSION: int = 512  # deprecated: 实际维度从 embedding 模型自动探测（bge-small-zh-v1.5=512）

    # --- JWT ---
    SECRET_KEY: str = "medical-consultant-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: str = '["*"]'

    # --- Knowledge Base ---
    MEDICAL_KB_PATH: str = "./data/medical_kb"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    CHUNK_MIN_SIZE: int = 50  # 丢弃小于此长度的尾块
    TOP_K_RETRIEVAL: int = 5
    SCORE_THRESHOLD: float = 0.2  # 稠密检索最低相似度
    RRF_K: int = 60  # RRF 融合参数 k (越大越平滑)
    QUERY_EXPANSION: str = "dict"  # query 改写方法: dict (默认) / llm / none
    # Rerank
    RERANK_MODEL: str = "BAAI/bge-reranker-base"
    RERANK_CANDIDATES: int = 0  # 0=关闭, >0=送 rerank 的候选数
    RERANK_TOP_K: int = 10
    RERANK_BATCH_SIZE: int = 8

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_cors_origins(self) -> List[str]:
        import json
        try:
            return json.loads(self.CORS_ORIGINS)
        except Exception:
            return ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
