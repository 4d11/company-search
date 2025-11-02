from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Database settings
    database_url: str

    # Elasticsearch settings
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_api_key: Optional[str] = None

    # Embedding model settings
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_dimensions: int = 1024

    llm_model: str = "gpt-4o-mini"
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None

    use_llm_cache: bool = True
    llm_cache_db_path: str = str(Path(__file__).parent.parent / ".llm_cache.db")

    log_level: str = "INFO"


settings = Settings()