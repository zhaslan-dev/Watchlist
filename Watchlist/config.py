from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., description="Telegram bot token")
    KINOPOISK_API_KEY: str = Field(..., description="Kinopoisk API key")
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./watchlist.db",
        description="Database URL (sqlite+aiosqlite:///./watchlist.db или postgresql+asyncpg://...)",
    )
    REDIS_URL: Optional[str] = Field(default=None, description="Redis URL (оставьте None, если не нужен)")
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="logs/bot.log")
    VOTE_THRESHOLD: int = Field(default=2)
    MIN_VOTERS: int = Field(default=2)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)

settings = Settings()