"""
Определение Celery-задач для фонового выполнения (опционально).
"""

import asyncio
import time
from loguru import logger

# Попытка импортировать Celery, если он установлен
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    # Создаём заглушку декоратора shared_task, чтобы не падал импорт
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        # Если декоратор использован без аргументов (с функцией)
        if args and callable(args[0]):
            return decorator(args[0])
        return decorator

# Глобальный объект бота (будет инициализирован позже)
_bot = None

def set_bot(bot):
    global _bot
    _bot = bot

def get_bot():
    return _bot

# ------------------ Задачи ------------------
if CELERY_AVAILABLE:
    @shared_task(name="send_reminder")
    def send_reminder(chat_id: int, text: str, delay_seconds: int = 0):
        """Отправляет напоминание через заданное количество секунд."""
        if delay_seconds > 0:
            time.sleep(delay_seconds)

        # Для отправки сообщения используем синхронную обёртку
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # Импортируем Bot только здесь, чтобы избежать циклических импортов
            from aiogram import Bot
            from Watchlist.config import settings
            if _bot:
                bot = _bot
            else:
                bot = Bot(token=settings.BOT_TOKEN)
            loop.run_until_complete(bot.send_message(chat_id=chat_id, text=text))
            loop.close()
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")
        return f"Reminder sent to {chat_id}"

    @shared_task(name="cleanup_old_votes")
    def cleanup_old_votes(days: int = 7):
        """Очистка старых голосов (заглушка)."""
        from Watchlist.infrastructure.db.session import async_session_maker
        from Watchlist.infrastructure.db.repositories import VoteRepository
        import asyncio

        async def _cleanup():
            async with async_session_maker() as session:
                repo = VoteRepository(session)
                logger.info(f"Cleaning up votes older than {days} days")
                await session.commit()

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_cleanup())
            loop.close()
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return "Failed"
        return "Done"

else:
    # Заглушки, если Celery не установлен
    def send_reminder(chat_id: int, text: str, delay_seconds: int = 0):
        logger.warning("Celery not installed, reminder not sent")
        return "Celery not installed"

    def cleanup_old_votes(days: int = 7):
        logger.warning("Celery not installed, cleanup skipped")
        return "Celery not installed"

# Асинхронные обёртки для вызова из бота
async def send_reminder_async(chat_id: int, text: str, delay_seconds: int = 0):
    """Отправляет задачу в Celery (если доступен), иначе лог."""
    if CELERY_AVAILABLE:
        send_reminder.apply_async(args=[chat_id, text, delay_seconds])
        logger.debug(f"Reminder scheduled for {chat_id} after {delay_seconds}s")
    else:
        logger.warning("Celery not installed, reminder not scheduled")
        # Можно отправить напоминание немедленно, но в фоне? Не будем усложнять.
        # Просто выведем предупреждение.