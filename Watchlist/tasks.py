# Watchlist/tasks.py
"""
Определение Celery-задач для фонового выполнения.
"""

import asyncio
from celery import shared_task
from aiogram import Bot
from loguru import logger
from Watchlist.config import settings

_bot = None

def get_bot():
    global _bot
    if _bot is None:
        _bot = Bot(token=settings.BOT_TOKEN)
    return _bot

@shared_task(name="send_reminder")
def send_reminder(chat_id: int, text: str, delay_seconds: int = 0):
    import time
    if delay_seconds > 0:
        time.sleep(delay_seconds)

    bot = get_bot()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.send_message(chat_id=chat_id, text=text))
        loop.close()
    except Exception as e:
        logger.error(f"Failed to send reminder: {e}")
    return f"Reminder sent to {chat_id}"

@shared_task(name="cleanup_old_votes")
def cleanup_old_votes(days: int = 7):
    from Watchlist.infrastructure.db.session import async_session_maker
    from Watchlist.infrastructure.db.repositories import VoteRepository
    import asyncio
    from loguru import logger

    async def _cleanup():
        async with async_session_maker() as session:
            repo = VoteRepository(session)
            # Пример: удаляем голоса, созданные раньше, чем days дней назад
            # from datetime import datetime, timedelta
            # threshold = datetime.now() - timedelta(days=days)
            # result = await repo.delete_older_than(threshold)
            logger.info(f"Cleaning up votes older than {days} days")
            # await session.commit()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_cleanup())
        loop.close()
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return "Failed"
    return "Done"

async def send_reminder_async(chat_id: int, text: str, delay_seconds: int = 0):
    send_reminder.apply_async(args=[chat_id, text, delay_seconds])

async def cleanup_old_votes_async(days: int = 7):
    cleanup_old_votes.apply_async(args=[days])