# backend/app/core/config.py
"""
Application configuration
"""
from pydantic_settings import BaseSettings
from typing import List, Optional # Tambahkan Optional


class Settings(BaseSettings):
    """Application settings"""

    # Project
    PROJECT_NAME: str = "Fund Performance Analysis System"
    VERSION: str = "1.0.0"

    # API
    API_V1_STR: str = "/api"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = "postgresql://funduser:fundpass@localhost:5432/funddb"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Google Generative AI (Gemini)
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-flash-latest"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"

    # --- TAMBAHKAN BARIS INI ---
    USE_LOCAL_EMBEDDINGS: bool = False  # <-- Set ke False untuk gunakan Google
    # LOCAL_EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5" # <-- Tidak digunakan jika USE_LOCAL_EMBEDDINGS=False
    # --------------------------

    # Anthropic (optional)
    ANTHROPIC_API_KEY: str = ""

    # Vector Store
    VECTOR_STORE_PATH: str = "./vector_store"
    FAISS_INDEX_PATH: str = "./faiss_index"

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # Document Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # RAG
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.7

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()