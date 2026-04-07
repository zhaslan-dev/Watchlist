import pytest
from unittest.mock import AsyncMock, MagicMock
from Watchlist.application.services.queue_service import QueueService
from Watchlist.domain.entities import QueueItem, VoteType, QueueItemStatus, MediaItem
from Watchlist.infrastructure.api.kinopoisk import KinopoiskError

@pytest.fixture
def queue_service_mocks():
    media_repo = AsyncMock()
    queue_repo = AsyncMock()
    queue_item_repo = AsyncMock()
    vote_repo = AsyncMock()
    history_repo = AsyncMock()
    kinopoisk = AsyncMock()
    bot = AsyncMock()
    return (media_repo, queue_repo, queue_item_repo, vote_repo, history_repo, kinopoisk, bot)

@pytest.fixture
def queue_service(queue_service_mocks):
    media_repo, queue_repo, queue_item_repo, vote_repo, history_repo, kinopoisk, bot = queue_service_mocks
    return QueueService(media_repo, queue_repo, queue_item_repo, vote_repo, history_repo, kinopoisk, bot)

@pytest.mark.asyncio
async def test_vote_new_vote(queue_service, queue_service_mocks):
    media_repo, queue_repo, queue_item_repo, vote_repo, history_repo, kinopoisk, bot = queue_service_mocks
    queue_item = QueueItem(id=1, queue_id=1, media_id=1, added_by=123, votes_for=0, votes_against=0)
    queue_item_repo.get_item.return_value = queue_item
    queue_item_repo.update_item.return_value = queue_item
    vote_repo.get_user_vote.return_value = None
    result = await queue_service.vote(1, 456, VoteType.FOR)
    assert result.votes_for == 1
    assert result.votes_against == 0
    vote_repo.add_vote.assert_called_once()
    queue_item_repo.update_item.assert_called_once()

@pytest.mark.asyncio
async def test_vote_change_vote(queue_service, queue_service_mocks):
    media_repo, queue_repo, queue_item_repo, vote_repo, history_repo, kinopoisk, bot = queue_service_mocks
    queue_item = QueueItem(id=1, queue_id=1, media_id=1, added_by=123, votes_for=1, votes_against=0)
    queue_item_repo.get_item.return_value = queue_item
    queue_item_repo.update_item.return_value = queue_item
    existing_vote = MagicMock(vote_type=VoteType.FOR)
    vote_repo.get_user_vote.return_value = existing_vote
    result = await queue_service.vote(1, 456, VoteType.AGAINST)
    assert result.votes_for == 0
    assert result.votes_against == 1
    vote_repo.update_vote.assert_called_once_with(existing_vote)
    assert existing_vote.vote_type == VoteType.AGAINST

@pytest.mark.asyncio
async def test_add_media_new(queue_service, queue_service_mocks):
    media_repo, queue_repo, queue_item_repo, vote_repo, history_repo, kinopoisk, bot = queue_service_mocks
    media_repo.get_by_external_id.return_value = None
    movie = MagicMock()
    kinopoisk.get_movie_by_id.return_value = movie
    kinopoisk.convert_to_media_item.return_value = MediaItem(id=None, external_id="123", title="Test")
    media_repo.add.return_value = MediaItem(id=1, external_id="123", title="Test")
    queue = MagicMock(id=1)
    queue_repo.get_queue_by_chat.return_value = None
    queue_repo.create_queue.return_value = queue
    new_item = QueueItem(id=1, queue_id=1, media_id=1, added_by=456)
    queue_item_repo.add_item.return_value = new_item
    result = await queue_service.add_media_from_kinopoisk(12345, "123", 456)
    assert result.id == 1
    media_repo.add.assert_called_once()
    queue_item_repo.add_item.assert_called_once()

@pytest.mark.asyncio
async def test_add_media_existing(queue_service, queue_service_mocks):
    media_repo, queue_repo, queue_item_repo, vote_repo, history_repo, kinopoisk, bot = queue_service_mocks
    existing_media = MediaItem(id=1, external_id="123", title="Test")
    media_repo.get_by_external_id.return_value = existing_media
    queue = MagicMock(id=1)
    queue_repo.get_queue_by_chat.return_value = queue
    new_item = QueueItem(id=2, queue_id=1, media_id=1, added_by=456)
    queue_item_repo.add_item.return_value = new_item
    result = await queue_service.add_media_from_kinopoisk(12345, "123", 456)
    assert result.id == 2
    kinopoisk.get_movie_by_id.assert_not_called()
    media_repo.add.assert_not_called()