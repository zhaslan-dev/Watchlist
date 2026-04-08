import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from Watchlist.infrastructure.db.repositories import MediaRepository
from Watchlist.domain.entities import MediaItem, MediaSource
from Watchlist.infrastructure.db.models import Base

@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = AsyncSession(engine)
    yield async_session
    await async_session.close()
    await engine.dispose()

@pytest.mark.asyncio
async def test_media_repository_add_and_get(test_session: AsyncSession):
    """Тест добавления и получения медиа."""
    repo = MediaRepository(test_session)
    media = MediaItem(external_id="ext1", title="Title", source=MediaSource.KINOPOISK)
    added = await repo.add(media)
    assert added.id is not None
    fetched = await repo.get_by_external_id("ext1")
    assert fetched is not None
    assert fetched.title == "Title"
    assert fetched.source == MediaSource.KINOPOISK