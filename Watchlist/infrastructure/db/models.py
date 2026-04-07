from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, BigInteger
from sqlalchemy.sql import func
from Watchlist.infrastructure.db.base import Base
from Watchlist.domain.entities import MediaSource, QueueItemStatus, VoteType

class MediaItemDB(Base):
    __tablename__ = "media_items"
    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    poster_url = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    year = Column(String, nullable=True)
    director = Column(String, nullable=True)
    source = Column(SQLEnum(MediaSource, native_enum=False), default=MediaSource.KINOPOISK)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class QueueDB(Base):
    __tablename__ = "queues"
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    chat_type = Column(String(20), nullable=False, default="private")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class QueueItemDB(Base):
    __tablename__ = "queue_items"
    id = Column(Integer, primary_key=True)
    queue_id = Column(Integer, ForeignKey("queues.id", ondelete="CASCADE"), nullable=False)
    media_id = Column(Integer, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False)
    added_by = Column(BigInteger, nullable=False)
    status = Column(SQLEnum(QueueItemStatus, native_enum=False), default=QueueItemStatus.PENDING)
    votes_for = Column(Integer, default=0)
    votes_against = Column(Integer, default=0)
    message_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class VoteDB(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True)
    queue_item_id = Column(Integer, ForeignKey("queue_items.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    vote_type = Column(SQLEnum(VoteType, native_enum=False), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WatchedHistoryDB(Base):
    __tablename__ = "watched_history"
    id = Column(Integer, primary_key=True)
    queue_item_id = Column(Integer, ForeignKey("queue_items.id", ondelete="SET NULL"), nullable=True)
    media_id = Column(Integer, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    user_rating = Column(Integer, nullable=True)
    accepted_by = Column(BigInteger, nullable=True)
    accepted_at = Column(DateTime(timezone=True), server_default=func.now())