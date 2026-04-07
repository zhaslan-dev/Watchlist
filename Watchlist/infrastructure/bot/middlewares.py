import uuid
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from loguru import logger
from Watchlist.infrastructure.api.kinopoisk import KinopoiskError, get_kinopoisk_client
from Watchlist.application.services.queue_service import QueueService
from Watchlist.infrastructure.db.repositories import (
    MediaRepository, QueueRepository, QueueItemRepository, VoteRepository, WatchedHistoryRepository
)
from Watchlist.config import settings

class DBSessionMiddleware(BaseMiddleware):
    def __init__(self, session_maker: async_sessionmaker):
        self.session_maker = session_maker

    async def __call__(self, handler, event, data):
        async with self.session_maker() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

class RequestIdMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        request_id = str(uuid.uuid4())
        data["request_id"] = request_id
        with logger.contextualize(request_id=request_id):
            return await handler(event, data)

class ServiceFactoryMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def __call__(self, handler, event, data):
        session: AsyncSession = data.get("session")
        if not session:
            return await handler(event, data)
        media_repo = MediaRepository(session)
        queue_repo = QueueRepository(session)
        queue_item_repo = QueueItemRepository(session)
        vote_repo = VoteRepository(session)
        history_repo = WatchedHistoryRepository(session)
        kinopoisk_client = get_kinopoisk_client()
        queue_service = QueueService(
            media_repo, queue_repo, queue_item_repo, vote_repo, history_repo,
            kinopoisk_client, self.bot
        )
        data["queue_service"] = queue_service
        data["kinopoisk_client"] = kinopoisk_client
        return await handler(event, data)

class ErrorHandlingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except KinopoiskError as e:
            logger.error(f"Kinopoisk error: {e}")
            await event.answer("❌ Ошибка при работе с Кинопоиском. Попробуйте позже.")
        except ValueError as e:
            logger.warning(f"Value error: {e}")
            await event.answer(f"❌ Ошибка: {e}")
        except Exception as e:
            logger.exception(f"Unhandled exception: {e}")
            await event.answer("❌ Произошла непредвиденная ошибка. Администраторы уже уведомлены.")

class AccessMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = None
        chat_id = None

        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id
        elif hasattr(event, "message") and event.message and event.message.from_user:
            user_id = event.message.from_user.id

        if hasattr(event, "chat") and event.chat:
            chat_id = event.chat.id
        elif hasattr(event, "message") and event.message and event.message.chat:
            chat_id = event.message.chat.id

        if settings.ALLOWED_USER_IDS and user_id not in settings.ALLOWED_USER_IDS:
            await event.answer("⛔ Доступ запрещён. Этот бот для личного использования.")
            return

        if settings.ALLOWED_CHAT_IDS and chat_id not in settings.ALLOWED_CHAT_IDS:
            await event.answer("⛔ Бот работает только в разрешённых чатах.")
            return

        return await handler(event, data)