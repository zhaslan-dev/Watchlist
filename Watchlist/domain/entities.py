from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class MediaSource(str, Enum):
    KINOPOISK = "kinopoisk"
    MANUAL = "manual"

class VoteType(str, Enum):
    FOR = "for"
    AGAINST = "against"

class QueueItemStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class MediaItem(BaseModel):
    id: Optional[int] = None
    external_id: str
    title: str
    description: Optional[str] = None
    poster_url: Optional[str] = None
    rating: Optional[float] = None
    year: Optional[str] = None
    director: Optional[str] = None
    source: MediaSource = MediaSource.KINOPOISK
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Queue(BaseModel):
    id: Optional[int] = None
    chat_id: int
    title: str = "Общая очередь"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QueueItem(BaseModel):
    id: Optional[int] = None
    queue_id: int
    media_id: int
    added_by: int
    status: QueueItemStatus = QueueItemStatus.PENDING
    votes_for: int = 0
    votes_against: int = 0
    message_id: Optional[int] = None   # ID сообщения в Telegram с кнопками
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Vote(BaseModel):
    id: Optional[int] = None
    queue_item_id: int
    user_id: int
    vote_type: VoteType
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WatchedHistory(BaseModel):
    id: Optional[int] = None
    queue_item_id: int
    media_id: int
    chat_id: int
    accepted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    accepted_by: Optional[int] = None