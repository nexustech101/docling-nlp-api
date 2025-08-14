from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Configuration
    app_name: str = "Docling NLP API"
    version: str = "1.0.0"
    debug: bool = False

    # File handling
    upload_dir: str = "uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list = [
        '.pdf', '.docx', '.doc', '.html', '.txt', '.md'
    ]

    # Docling Configuration
    docling_cache_size: int = 1
    enable_ocr: bool = True

    # URL Processing
    url_timeout: int = 30
    max_url_file_size: int = 100 * 1024 * 1024  # 100MB

    # Logging
    log_level: str = "INFO"

    # Firebase Configuration
    firebase_project_id: Optional[str] = None
    firebase_credentials_path: Optional[str] = None
    firebase_service_account_key: Optional[str] = None  # JSON string

    # Rate Limiting Configuration
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    rate_limit_per_day: int = 10000
    redis_url: str = "redis://localhost:6379"
    enable_rate_limiting: bool = True

    # API Token Configuration
    api_token_expiry_days: int = 30
    max_api_tokens_per_user: int = 5
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
