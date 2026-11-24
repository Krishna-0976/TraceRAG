import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = "TraceRAG"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./tracerag.db",
        description="Database connection URL (PostgreSQL + pgvector or SQLite)"
    )
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    
    # LLM & Embedding Settings
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_BASE_URL: Optional[str] = Field(default=None)
    EMBEDDING_PROVIDER: str = "openai"  # "openai", "local", "mock"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536
    LLM_MODEL: str = "gpt-4o-mini"
    EVAL_JUDGE_MODEL: str = "gpt-4o-mini"
    
    # Ingestion & Retrieval Defaults
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_CHUNK_OVERLAP: int = 100
    DEFAULT_TOP_K: int = 4
    DEFAULT_SIMILARITY_THRESHOLD: float = 0.40

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
