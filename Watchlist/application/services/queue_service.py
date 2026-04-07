import asyncio
from typing import List, Optional
from loguru import logger
from Watchlist.domain.entities import MediaItem, Queue, QueueItem, Vote, VoteType, QueueItemStatus, WatchedHistory
from Watchlist.domain.interfaces import (
    IMediaRepository, IQueueRepository, IQueueItemRepository, IVoteRepository, IWatchedHistoryRepository
)
from Watchlist.infrastructure.api.kinopoisk import KinopoiskClient, KinopoiskError
from Watchlist.config import settings
from Watchlist.infrastructure.bot.keyboards import media_links_keyboard, rating_keyboard

class QueueService:
    def __init__(
        self,
        media_repo: IMediaRepository,
        queue_repo: IQueueRepository,
        queue_item_repo: IQueueItemRepository,
        vote_repo: IVoteRepository,
        history_repo: IWatchedHistoryRepository,
        kinopoisk_client: KinopoiskClient,
        bot,
    ):
        self.media_repo = media_repo
        self.queue_repo = queue_repo
        self.queue_item_repo = queue_item_repo
        self.vote_repo = vote_repo
        self.history_repo = history_repo
        self.kinopoisk = kinopoisk_client
        self.bot = bot

    async def get_or_create_queue(self, chat_id: int) -> Queue:
        queue = await self.queue_repo.get_queue_by_chat(chat_id)
        if not queue:
            # Определяем тип чата через Telegram API
            chat = await self.bot.get_chat(chat_id)
            chat_type = chat.type  # 'private', 'group', 'supergroup'
            queue = await self.queue_repo.create_queue(chat_id, chat_type=chat_type)
            logger.info(f"Created new queue for chat {chat_id} of type {chat_type}")
        return queue

    async def add_media_from_kinopoisk(self, chat_id: int, kinopoisk_id: str, added_by: int) -> QueueItem:
        media = await self.media_repo.get_by_external_id(kinopoisk_id)
        if not media:
            try:
                movie = await self.kinopoisk.get_movie_by_id(int(kinopoisk_id))
                if not movie:
                    raise ValueError(f"Movie with id {kinopoisk_id} not found")
                media = await self.kinopoisk.convert_to_media_item(movie)
                media = await self.media_repo.add(media)
                logger.info(f"Added new media: {media.title}")
            except KinopoiskError as e:
                logger.error(f"Kinopoisk API error: {e}")
                raise
        queue = await self.get_or_create_queue(chat_id)
        queue_item = QueueItem(queue_id=queue.id, media_id=media.id, added_by=added_by)
        queue_item = await self.queue_item_repo.add_item(queue_item)
        logger.info(f"Added item {queue_item.id} to queue {queue.id}")
        return queue_item

    async def vote(self, queue_item_id: int, user_id: int, vote_type: VoteType) -> QueueItem:
        queue_item = await self.queue_item_repo.get_item(queue_item_id)
        if not queue_item:
            raise ValueError("Queue item not found")

        existing_vote = await self.vote_repo.get_user_vote(queue_item_id, user_id)

        if existing_vote:
            if existing_vote.vote_type == VoteType.FOR:
                queue_item.votes_for -= 1
            else:
                queue_item.votes_against -= 1
            existing_vote.vote_type = vote_type
            await self.vote_repo.update_vote(existing_vote)
        else:
            vote = Vote(queue_item_id=queue_item_id, user_id=user_id, vote_type=vote_type)
            await self.vote_repo.add_vote(vote)

        if vote_type == VoteType.FOR:
            queue_item.votes_for += 1
        else:
            queue_item.votes_against += 1

        queue_item = await self.queue_item_repo.update_item(queue_item)
        # Проверяем принятие асинхронно, но можно и синхронно
        asyncio.create_task(self._check_and_accept(queue_item))
        return queue_item

    async def _check_and_accept(self, item: QueueItem):
        queue = await self.queue_repo.get_queue_by_id(item.queue_id)
        if not queue:
            logger.error(f"Queue not found for item {item.id}")
            return

        # Определяем порог в зависимости от типа чата
        if queue.chat_type == "private":
            threshold = 1
            min_voters = 1
        else:
            threshold = settings.VOTE_THRESHOLD
            min_voters = settings.MIN_VOTERS

        logger.debug(f"Item {item.id}: votes_for={item.votes_for}, votes_against={item.votes_against}, threshold={threshold}, min_voters={min_voters}")

        if (item.votes_for - item.votes_against >= threshold and
            item.votes_for + item.votes_against >= min_voters and
            item.status == QueueItemStatus.PENDING):
            item.status = QueueItemStatus.ACCEPTED
            await self.queue_item_repo.update_item(item)
            logger.info(f"Queue item {item.id} accepted in {queue.chat_type} chat")

            # Сохраняем в историю (без оценки пока)
            history = WatchedHistory(
                queue_item_id=item.id,
                media_id=item.media_id,
                chat_id=queue.chat_id,
                accepted_by=None,
            )
            await self.history_repo.add(history)

            # Отправляем сообщение с ссылками на кинотеатры
            media = await self.media_repo.get_by_id(item.media_id)
            if media:
                text = f"✅ *{media.title}* одобрен для просмотра!\n\nГде смотреть:"
                markup = media_links_keyboard(media.title, media.external_id)
                await self.bot.send_message(chat_id=queue.chat_id, text=text, reply_markup=markup, parse_mode="Markdown")

                # Через некоторое время запросим оценку (можно сразу или отдельным сообщением)
                await asyncio.sleep(2)
                rating_markup = rating_keyboard(item.id)
                await self.bot.send_message(
                    chat_id=queue.chat_id,
                    text=f"🎬 После просмотра оцените фильм *{media.title}* от 1 до 10:",
                    reply_markup=rating_markup,
                    parse_mode="Markdown"
                )

    async def get_queue_items(self, chat_id: int, status: Optional[QueueItemStatus] = QueueItemStatus.PENDING) -> List[QueueItem]:
        queue = await self.get_or_create_queue(chat_id)
        status_str = status.value if status else None
        items = await self.queue_item_repo.get_items_by_queue(queue.id, status_str)
        return items

    async def get_media_for_item(self, queue_item: QueueItem) -> Optional[MediaItem]:
        return await self.media_repo.get_by_id(queue_item.media_id)

    async def get_media_for_item_by_id(self, media_id: int) -> Optional[MediaItem]:
        return await self.media_repo.get_by_id(media_id)