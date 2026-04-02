import pytest
from unittest.mock import AsyncMock, MagicMock
from Watchlist.application.services.queue_service import QueueService
from Watchlist.domain.entities import QueueItem, VoteType, QueueItemStatus
from Watchlist.infrastructure.api.kinopoisk import KinopoiskClient, KinopoiskMovie, KinopoiskError

@pytest.mark.asyncio
async def test_vote_new_vote():
    media_repo = AsyncMock()
    queue_repo = AsyncMock()
    queue_item_repo = AsyncMock()
    vote_repo = AsyncMock()
    history_repo = AsyncMock()
    kinopoisk = AsyncMock(spec=KinopoiskClient)
    bot = AsyncMock()

    queue_item = QueueItem(id=1, queue_id=1, media_id=1, added_by=123, votes_for=0, votes_against=0, status=QueueItemStatus.PENDING)
    queue_item_repo.get_item.return_value = queue_item
    queue_item_repo.update_item.return_value = queue_item
    vote_repo.get_user_vote.return_value = None

    service = QueueService(media_repo, queue_repo, queue_item_repo, vote_repo, history_repo, kinopoisk, bot)

    result = await service.vote(1, 456, VoteType.FOR)

    assert result.votes_for == 1
    assert result.votes_against == 0
    vote_repo.add_vote.assert_called_once()
    queue_item_repo.update_item.assert_called_once()

@pytest.mark.asyncio
async def test_add_media_from_kinopoisk_new_media():
    media_repo = AsyncMock()
    queue_repo = AsyncMock()
    queue_item_repo = AsyncMock()
    vote_repo = AsyncMock()
    history_repo = AsyncMock()
    kinopoisk = AsyncMock(spec=KinopoiskClient)
    bot = AsyncMock()

    media_repo.get_by_external_id.return_value = None
    movie = KinopoiskMovie(kinopoiskId=123, nameRu="Test Movie", ratingKinopoisk=7.5)
    kinopoisk.get_movie_by_id.return_value = movie
    new_media = MagicMock(id=1)
    kinopoisk.convert_to_media_item.return_value = new_media
    media_repo.add.return_value = new_media

    queue = MagicMock(id=1)
    queue_repo.get_queue_by_chat.return_value = None
    queue_repo.create_queue.return_value = queue

    new_item = QueueItem(id=1, queue_id=1, media_id=1, added_by=456, status=QueueItemStatus.PENDING)
    queue_item_repo.add_item.return_value = new_item

    service = QueueService(media_repo, queue_repo, queue_item_repo, vote_repo, history_repo, kinopoisk, bot)

    result = await service.add_media_from_kinopoisk(12345, "123", 456)

    assert result.id == 1
    media_repo.add.assert_called()
    queue_item_repo.add_item.assert_called()