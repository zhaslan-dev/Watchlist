from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from Watchlist.config import settings

if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)