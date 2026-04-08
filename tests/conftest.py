import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from Watchlist.infrastructure.db.models import Base
from Watchlist.application.services.queue_service import QueueService
from unittest.mock import AsyncMock
import asyncio

@pytest.fixture(scope="function")
async def test_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()
    await engine.dispose()

@pytest.fixture
def queue_service_mocks():
    media_repo = AsyncMock()
    queue_repo = AsyncMock()
    queue_item_repo = AsyncMock()
    vote_repo = AsyncMock()
    history_repo = AsyncMock()
    kinopoisk = AsyncMock()
    bot = AsyncMock()
    mock_chat = AsyncMock()
    mock_chat.type = "private"
    bot.get_chat = AsyncMock(return_value=mock_chat)
    return (media_repo, queue_repo, queue_item_repo, vote_repo, history_repo, kinopoisk, bot)

@pytest.fixture
def queue_service(queue_service_mocks):
    media_repo, queue_repo, queue_item_repo, vote_repo, history_repo, kinopoisk, bot = queue_service_mocks
    return QueueService(
        media_repo, queue_repo, queue_item_repo, vote_repo, history_repo, kinopoisk, bot
    )

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()