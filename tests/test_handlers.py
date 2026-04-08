"""
Тесты хендлеров Telegram (с моками aiogram).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, CallbackQuery, User, Chat
from Watchlist.infrastructure.bot.handlers.commands import cmd_start, cmd_search, select_movie

@pytest.fixture
def mock_message():
    msg = AsyncMock(spec=Message)
    msg.from_user = MagicMock(id=123)
    msg.chat = MagicMock(id=456)
    msg.text = "/start"
    msg.answer = AsyncMock()
    return msg

@pytest.mark.asyncio
async def test_cmd_start(mock_message):
    state = AsyncMock()
    await cmd_start(mock_message, state)
    mock_message.answer.assert_called_once()
    state.clear.assert_called_once()