"""
AppConfig - Singleton Pattern
Centralized configuration management
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Expense Tracker API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""

    # CORS
    ALLOWED_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


# ============================================
# SINGLETON via lru_cache
# ============================================
@lru_cache()
def get_settings() -> Settings:
    """Returns singleton Settings instance"""
    return Settings()


# Global instance
settings = get_settings()
