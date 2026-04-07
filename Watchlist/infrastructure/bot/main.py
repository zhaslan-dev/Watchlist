from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from loguru import logger
from Watchlist.config import settings
from Watchlist.infrastructure.bot.handlers import commands, callbacks
from Watchlist.infrastructure.bot.middlewares import (
    DBSessionMiddleware,
    RequestIdMiddleware,
    ServiceFactoryMiddleware,
    ErrorHandlingMiddleware,
    AccessMiddleware,
)
from Watchlist.infrastructure.db.session import async_session_maker
from Watchlist.infrastructure.metrics import start_metrics_server
from Watchlist.infrastructure.db.session import engine
from Watchlist.infrastructure.db.models import Base

bot = None

async def on_startup(bot: Bot):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Bot started")

async def on_shutdown(bot: Bot):
    logger.info("Bot stopping...")
    await bot.session.close()

async def set_commands(bot: Bot) -> None:
    commands_list = [
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="search", description="Поиск фильмов"),
        BotCommand(command="queue", description="Показать очередь"),
        BotCommand(command="history", description="История просмотренных"),
        BotCommand(command="help", description="Помощь"),
    ]
    await bot.set_my_commands(commands_list)

async def start_bot() -> None:
    global bot
    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.middleware(DBSessionMiddleware(async_session_maker))
    dp.callback_query.middleware(DBSessionMiddleware(async_session_maker))
    dp.message.middleware(RequestIdMiddleware())
    dp.callback_query.middleware(RequestIdMiddleware())
    dp.message.middleware(ServiceFactoryMiddleware(bot))
    dp.callback_query.middleware(ServiceFactoryMiddleware(bot))
    dp.message.middleware(ErrorHandlingMiddleware())
    dp.callback_query.middleware(ErrorHandlingMiddleware())
    dp.message.middleware(AccessMiddleware())
    dp.callback_query.middleware(AccessMiddleware())

    dp.include_router(commands.router)
    dp.include_router(callbacks.router)

    await set_commands(bot)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")