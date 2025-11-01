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
    embedding_model_name: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384


# Global settings instance
settings = Settings()
