#!/usr/bin/env python
"""
Скрипт для создания таблиц в базе данных.
Запуск: python scripts/init_db.py
"""
import asyncio
from Watchlist.infrastructure.db.session import engine
from Watchlist.infrastructure.db.models import Base
from loguru import logger

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

if __name__ == "__main__":
    asyncio.run(init_db())