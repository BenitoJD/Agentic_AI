"""Application configuration."""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    llm_preference: str = "gemini"  # auto | ollama | openai | gemini
    temperature: float = 0.35

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    ollama_base_url: Optional[str] = "http://localhost:11434"
    ollama_model: str = "deepseek-r1:8b"

    gemini_api_key: Optional[str] = ""
    gemini_model: str = "gemini-2.0-flash-lite"

    embedding_preference: str = "ollama"  # ollama | openai
    ollama_embedding_model: str = "embeddinggemma"
    openai_embedding_model: str = "text-embedding-3-small"

    default_skill_packs: List[str] = []
    allowed_origins: List[str] = ["*"]

    redis_url: Optional[str] = None
    vector_store_path: str = "./data/vector-store"
    vector_collection: str = "uploaded_docs"


@lru_cache(maxsize=1)
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()

