"""
Тесты репозиториев с реальной in-memory SQLite базой данных.
"""
import pytest
from Watchlist.infrastructure.db.repositories import (
    MediaRepository, QueueRepository, QueueItemRepository, VoteRepository
)
from Watchlist.domain.entities import (
    MediaItem, MediaSource, Queue, QueueItem, Vote, VoteType, QueueItemStatus
)

@pytest.mark.asyncio
async def test_media_repository_add_and_get(test_session):
    repo = MediaRepository(test_session)
    media = MediaItem(external_id="ext123", title="Test Movie", rating=8.5)
    added = await repo.add(media)
    assert added.id is not None

    fetched = await repo.get_by_external_id("ext123")
    assert fetched is not None
    assert fetched.title == "Test Movie"

    fetched_by_id = await repo.get_by_id(added.id)
    assert fetched_by_id is not None
    assert fetched_by_id.external_id == "ext123"

@pytest.mark.asyncio
async def test_queue_repository_create_and_get(test_session):
    repo = QueueRepository(test_session)
    queue = await repo.create_queue(chat_id=12345, title="My Queue", chat_type="private")
    assert queue.id is not None
    assert queue.chat_id == 12345
    assert queue.chat_type == "private"

    fetched = await repo.get_queue_by_chat(12345)
    assert fetched is not None
    assert fetched.title == "My Queue"

    fetched_by_id = await repo.get_queue_by_id(queue.id)
    assert fetched_by_id is not None
    assert fetched_by_id.chat_id == 12345

@pytest.mark.asyncio
async def test_queue_item_repository_add_and_update(test_session):
    queue_repo = QueueRepository(test_session)
    queue = await queue_repo.create_queue(chat_id=12345)

    media_repo = MediaRepository(test_session)
    media = await media_repo.add(MediaItem(external_id="ext", title="Title"))

    item_repo = QueueItemRepository(test_session)
    item = QueueItem(queue_id=queue.id, media_id=media.id, added_by=123)
    added = await item_repo.add_item(item)
    assert added.id is not None
    assert added.status == QueueItemStatus.PENDING

    added.votes_for = 1
    added.status = QueueItemStatus.ACCEPTED
    updated = await item_repo.update_item(added)
    assert updated.votes_for == 1
    assert updated.status == QueueItemStatus.ACCEPTED

    fetched = await item_repo.get_item(added.id)
    assert fetched is not None
    assert fetched.status == QueueItemStatus.ACCEPTED

    items = await item_repo.get_items_by_queue(queue.id)
    assert len(items) == 1

@pytest.mark.asyncio
async def test_vote_repository_add_and_update(test_session):
    queue_repo = QueueRepository(test_session)
    queue = await queue_repo.create_queue(chat_id=12345)
    media_repo = MediaRepository(test_session)
    media = await media_repo.add(MediaItem(external_id="ext", title="Title"))
    item_repo = QueueItemRepository(test_session)
    item = await item_repo.add_item(QueueItem(queue_id=queue.id, media_id=media.id, added_by=123))

    vote_repo = VoteRepository(test_session)
    vote = Vote(queue_item_id=item.id, user_id=456, vote_type=VoteType.FOR)
    added = await vote_repo.add_vote(vote)
    assert added.id is not None

    fetched = await vote_repo.get_user_vote(item.id, 456)
    assert fetched is not None
    assert fetched.vote_type == VoteType.FOR

    fetched.vote_type = VoteType.AGAINST
    updated = await vote_repo.update_vote(fetched)
    assert updated.vote_type == VoteType.AGAINST