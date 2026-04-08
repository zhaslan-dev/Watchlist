"""
Тесты доменных сущностей (Pydantic модели).
"""
import pytest
from datetime import datetime, timezone
from Watchlist.domain.entities import (
    MediaSource, VoteType, QueueItemStatus,
    MediaItem, Queue, QueueItem, Vote, WatchedHistory
)

def test_media_source_enum():
    assert MediaSource.KINOPOISK == "kinopoisk"
    assert MediaSource.MANUAL == "manual"

def test_vote_type_enum():
    assert VoteType.FOR == "for"
    assert VoteType.AGAINST == "against"

def test_queue_item_status_enum():
    assert QueueItemStatus.PENDING == "pending"
    assert QueueItemStatus.ACCEPTED == "accepted"
    assert QueueItemStatus.REJECTED == "rejected"

def test_media_item_defaults():
    item = MediaItem(external_id="123", title="Test")
    assert item.source == MediaSource.KINOPOISK
    assert item.created_at.tzinfo == timezone.utc
    assert item.id is None
    assert item.description is None

def test_queue_item_defaults():
    item = QueueItem(queue_id=1, media_id=1, added_by=123)
    assert item.status == QueueItemStatus.PENDING
    assert item.votes_for == 0
    assert item.votes_against == 0
    assert item.created_at.tzinfo == timezone.utc

def test_watched_history_optional_fields():
    history = WatchedHistory(queue_item_id=1, media_id=1, chat_id=123)
    assert history.user_rating is None
    assert history.accepted_by is None