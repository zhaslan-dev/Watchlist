import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., description="Telegram bot token")
    KINOPOISK_API_KEY: str = Field(..., description="Kinopoisk API key")
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./watchlist.db",
        description="Database URL"
    )
    REDIS_URL: Optional[str] = Field(default=None, description="Redis URL")
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="logs/bot.log")
    VOTE_THRESHOLD: int = Field(default=2)
    MIN_VOTERS: int = Field(default=2)

    # Для ограничения доступа
    ALLOWED_USER_IDS_STR: str = Field(default="", env="ALLOWED_USER_IDS")
    ALLOWED_CHAT_IDS_STR: str = Field(default="", env="ALLOWED_CHAT_IDS")

    @property
    def ALLOWED_USER_IDS(self) -> List[int]:
        return self._parse_ids(self.ALLOWED_USER_IDS_STR)

    @property
    def ALLOWED_CHAT_IDS(self) -> List[int]:
        return self._parse_ids(self.ALLOWED_CHAT_IDS_STR)

    def _parse_ids(self, v: str) -> List[int]:
        if not v or not v.strip():
            return []
        return [int(x.strip()) for x in v.split(",") if x.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()