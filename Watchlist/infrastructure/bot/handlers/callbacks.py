import re
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from Watchlist.application.services.queue_service import QueueService
from Watchlist.infrastructure.bot.keyboards import vote_keyboard
from Watchlist.domain.entities import VoteType, QueueItemStatus, WatchedHistory
from Watchlist.infrastructure.metrics import VOTE_COUNT

router = Router()

@router.callback_query(F.data.startswith("vote_"))
async def process_vote(callback: CallbackQuery, queue_service: QueueService):
    match = re.match(r"vote_(\d+)_(for|against)", callback.data)
    if not match:
        await callback.answer("Неверный формат")
        return

    item_id = int(match.group(1))
    vote_str = match.group(2)
    vote_type = VoteType.FOR if vote_str == "for" else VoteType.AGAINST
    VOTE_COUNT.labels(vote_type=vote_type.value).inc()

    try:
        updated_item = await queue_service.vote(item_id, callback.from_user.id, vote_type)
        await callback.answer(f"Ваш голос учтён! 👍 {updated_item.votes_for} | 👎 {updated_item.votes_against}")

        # Если элемент уже принят, удаляем кнопки
        if updated_item.status != QueueItemStatus.PENDING and updated_item.message_id:
            try:
                queue = await queue_service.queue_repo.get_queue_by_id(updated_item.queue_id)
                if queue:
                    await callback.bot.edit_message_reply_markup(
                        chat_id=queue.chat_id,
                        message_id=updated_item.message_id,
                        reply_markup=None
                    )
            except Exception:
                pass
        else:
            try:
                await callback.message.edit_reply_markup(reply_markup=vote_keyboard(item_id))
            except TelegramBadRequest:
                pass
    except Exception as e:
        logger.exception(f"Error processing vote: {e}")
        await callback.answer("Произошла ошибка при голосовании", show_alert=True)

@router.callback_query(F.data.startswith("rate_"))
async def process_rating(callback: CallbackQuery, session: AsyncSession, queue_service: QueueService):
    _, item_id_str, rating_str = callback.data.split("_")
    item_id = int(item_id_str)
    rating = int(rating_str)

    # Находим элемент очереди
    queue_item = await queue_service.queue_item_repo.get_item(item_id)
    if not queue_item or queue_item.status != QueueItemStatus.ACCEPTED:
        await callback.answer("Этот фильм уже был оценён или не найден.")
        return

    # Обновляем историю: добавляем оценку
    # Сначала ищем существующую запись истории по queue_item_id
    # В простом варианте создадим новую (если не хотим искать)
    # Лучше получить последнюю запись для этого элемента
    history = WatchedHistory(
        queue_item_id=item_id,
        media_id=queue_item.media_id,
        chat_id=callback.message.chat.id,
        user_rating=rating,
        accepted_by=callback.from_user.id,
    )
    await queue_service.history_repo.add(history)
    await callback.message.edit_text(f"🎬 Спасибо за оценку {rating}/10!")
    await callback.message.edit_reply_markup()
    await callback.answer()