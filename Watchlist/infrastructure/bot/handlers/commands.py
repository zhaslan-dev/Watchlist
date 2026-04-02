import asyncio
from typing import List
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from Watchlist.application.services.queue_service import QueueService
from Watchlist.infrastructure.api.kinopoisk import KinopoiskClient, KinopoiskError
from Watchlist.infrastructure.bot.keyboards import (
    main_menu_keyboard,
    vote_keyboard,
    pagination_keyboard,
    search_results_keyboard,
)
from Watchlist.config import settings
from Watchlist.domain.entities import VoteType
from Watchlist.infrastructure.metrics import REQUEST_COUNT, SEARCH_DURATION
from Watchlist.infrastructure.db.repositories import WatchedHistoryRepository

router = Router()

class SearchStates(StatesGroup):
    waiting_for_query = State()
    browsing_results = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    REQUEST_COUNT.labels(command="start").inc()
    await state.clear()
    await message.answer(
        "Привет! Это медиаочередь для совместного выбора.\n"
        "Используйте /search для поиска фильмов, /queue для просмотра очереди.",
        reply_markup=main_menu_keyboard(),
    )
    logger.info(f"User {message.from_user.id} started bot")

@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    REQUEST_COUNT.labels(command="search").inc()
    await message.answer("Введите название фильма, аниме или спектакля:")
    await state.set_state(SearchStates.waiting_for_query)
    logger.debug(f"User {message.from_user.id} initiated search")

@router.message(SearchStates.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext, kinopoisk_client: KinopoiskClient):
    query = message.text.strip()
    if not query:
        await message.answer("Пожалуйста, введите текст для поиска.")
        return

    loading_msg = await message.answer("🔍 Ищу фильмы...")
    try:
        with SEARCH_DURATION.time():
            movies = await kinopoisk_client.search_movies(query)
    except KinopoiskError as e:
        logger.error(f"Kinopoisk search error: {e}")
        await loading_msg.edit_text("❌ Ошибка при поиске. Попробуйте позже.")
        return

    if not movies:
        await loading_msg.edit_text("❌ Ничего не найдено.")
        await state.clear()
        return

    await loading_msg.delete()
    await state.update_data(search_results=movies, current_page=0, query=query)
    await send_search_page(message, state)

async def send_search_page(message: Message, state: FSMContext):
    data = await state.get_data()
    movies = data.get("search_results", [])
    page = data.get("current_page", 0)
    per_page = 5
    total_pages = (len(movies) + per_page - 1) // per_page
    start = page * per_page
    end = start + per_page
    page_movies = movies[start:end]

    text = f"Результаты поиска (страница {page+1} из {total_pages}):\nНажмите на кнопку с названием фильма, чтобы добавить в очередь."
    markup = search_results_keyboard(page_movies, page, total_pages)
    await message.answer(text, reply_markup=markup)
    await state.set_state(SearchStates.browsing_results)

@router.callback_query(F.data.startswith("search_page_"))
async def handle_search_pagination(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[-1])
    await state.update_data(current_page=page)
    await send_search_page(callback.message, state)
    await callback.answer()

@router.callback_query(F.data.startswith("select_movie_"))
async def select_movie(callback: CallbackQuery, state: FSMContext, queue_service: QueueService):
    movie_index = int(callback.data.split("_")[-1])
    data = await state.get_data()
    movies = data.get("search_results", [])
    if movie_index < 1 or movie_index > len(movies):
        await callback.answer("Неверный выбор")
        return

    selected_movie = movies[movie_index - 1]
    kinopoisk_id = selected_movie.kinopoiskId

    try:
        queue_item = await queue_service.add_media_from_kinopoisk(
            chat_id=callback.message.chat.id,
            kinopoisk_id=str(kinopoisk_id),
            added_by=callback.from_user.id,
        )
        # Отправляем карточку с кнопками голосования
        media = await queue_service.get_media_for_item(queue_item)
        if media and media.poster_url:
            caption = f"🎬 *{media.title}*"
            if media.year:
                caption += f" ({media.year})"
            if media.rating:
                caption += f"\n⭐ {media.rating}"
            if media.director:
                caption += f"\n🎥 {media.director}"
            if media.description:
                desc = media.description[:500]
                caption += f"\n\n{desc}..."
            msg = await callback.message.answer_photo(
                photo=media.poster_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=vote_keyboard(queue_item.id)
            )
        else:
            text = f"✅ Добавлено в очередь: {selected_movie.nameRu or selected_movie.nameEn}"
            msg = await callback.message.answer(text, reply_markup=vote_keyboard(queue_item.id))
        # Сохраняем message_id для возможности удаления кнопок
        queue_item.message_id = msg.message_id
        await queue_service.queue_item_repo.update_item(queue_item)
        logger.info(f"User {callback.from_user.id} added movie {kinopoisk_id}")
        await callback.answer("Добавлено!")
    except Exception as e:
        logger.exception(f"Error adding movie: {e}")
        await callback.answer("Ошибка добавления", show_alert=True)
    finally:
        await state.clear()

@router.message(Command("queue"))
async def cmd_queue(message: Message, queue_service: QueueService):
    REQUEST_COUNT.labels(command="queue").inc()
    items = await queue_service.get_queue_items(message.chat.id)
    if not items:
        await message.answer("Очередь пуста. Добавьте фильмы через /search")
        return

    text = "📋 *Текущая очередь:*\n"
    for idx, item in enumerate(items, 1):
        media = await queue_service.get_media_for_item(item)
        if media:
            title = media.title
            year = f" ({media.year})" if media.year else ""
            rating = f"⭐ {media.rating}" if media.rating else ""
            director = f"\n   🎥 {media.director}" if media.director else ""
            text += f"{idx}. *{title}{year}* {rating}\n{director}\n   👍 {item.votes_for} | 👎 {item.votes_against}\n\n"
        else:
            text += f"{idx}. *Неизвестное медиа* (id:{item.media_id})\n"
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("history"))
async def cmd_history(message: Message, session: AsyncSession, queue_service: QueueService):
    history_repo = WatchedHistoryRepository(session)
    history = await history_repo.get_by_chat(message.chat.id, limit=10)
    if not history:
        await message.answer("История пуста. Смотрите фильмы и они появятся здесь.")
        return
    text = "📜 *Недавно просмотренные:*\n"
    for idx, item in enumerate(history, 1):
        media = await queue_service.get_media_for_item_by_id(item.media_id)
        if media:
            text += f"{idx}. *{media.title}* — {item.accepted_at.strftime('%d.%m.%Y')}\n"
        else:
            text += f"{idx}. *Неизвестный фильм*\n"
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "Команды бота:\n"
        "/start - начать работу\n"
        "/search - поиск фильмов и добавление в очередь\n"
        "/queue - показать текущую очередь\n"
        "/history - показать историю просмотренных\n"
        "/help - эта справка\n\n"
        "Чтобы проголосовать за элемент очереди, нажмите кнопки под сообщением."
    )
    await message.answer(help_text)

@router.message(F.text == "🔍 Поиск")
async def text_search(message: Message, state: FSMContext):
    await cmd_search(message, state)

@router.message(F.text == "📋 Очередь")
async def text_queue(message: Message, queue_service: QueueService):
    await cmd_queue(message, queue_service)

@router.message(F.text == "❓ Помощь")
async def text_help(message: Message):
    await cmd_help(message)