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

    # LLM settings for attribute extraction
    llm_provider: str = "ollama"  # or "openai", "anthropic", etc.
    llm_model: str = "llama3.2:3b"
    llm_base_url: str = "http://localhost:11434"

    # LLM extraction cache settings (for LOCAL development only)
    use_llm_cache: bool = True
    llm_cache_db_path: str = str(Path(__file__).parent.parent / ".llm_cache.db")


# Global settings instance
settings = Settings()
