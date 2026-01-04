"""
Настройки приложения TrendScout

Этот файл загружает все переменные окружения из .env файла
и предоставляет удобный доступ к настройкам через класс Settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Класс для хранения всех настроек приложения.
    
    Pydantic автоматически загружает значения из переменных окружения
    и проверяет их типы.
    """
    
    # API Keys (опциональные - система работает и без них)
    apify_api_key: Optional[str] = Field(None, alias="APIFY_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    youtube_api_key: Optional[str] = Field(None, alias="YOUTUBE_API_KEY")
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    
    # Reddit API (опционально)
    reddit_client_id: Optional[str] = Field(None, alias="REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = Field(None, alias="REDDIT_CLIENT_SECRET")
    reddit_user_agent: str = Field("TrendScout/1.0", alias="REDDIT_USER_AGENT")
    
    # Database
    database_url: str = Field("sqlite:///./trendscout.db", alias="DATABASE_URL")
    
    # General Settings
    vertical: str = Field("coffee", alias="VERTICAL")
    location: Optional[str] = Field(None, alias="LOCATION")  # Например: "Chicago, IL" или "US-IL"
    debug: bool = Field(True, alias="DEBUG")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    
    class Config:
        env_file = ".env"  # Читать из .env файла
        env_file_encoding = "utf-8"
        case_sensitive = False


# Глобальный экземпляр настроек
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Получить настройки приложения (singleton pattern).
    
    Returns:
        Settings: Экземпляр настроек
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

