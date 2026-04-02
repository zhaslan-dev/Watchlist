from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from Watchlist.domain.entities import (
    MediaItem, Queue, QueueItem, Vote, VoteType,
    QueueItemStatus, WatchedHistory, MediaSource
)
from Watchlist.domain.interfaces import (
    IMediaRepository, IQueueRepository, IQueueItemRepository,
    IVoteRepository, IWatchedHistoryRepository
)
from .models import MediaItemDB, QueueDB, QueueItemDB, VoteDB, WatchedHistoryDB

class MediaRepository(IMediaRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, media: MediaItem) -> MediaItem:
        db_media = MediaItemDB(
            external_id=media.external_id,
            title=media.title,
            description=media.description,
            poster_url=media.poster_url,
            rating=media.rating,
            year=media.year,
            director=media.director,
            source=media.source.value,   # сохраняем строковое значение
        )
        self.session.add(db_media)
        await self.session.flush()
        media.id = db_media.id
        return media

    async def get_by_external_id(self, external_id: str) -> Optional[MediaItem]:
        stmt = select(MediaItemDB).where(MediaItemDB.external_id == external_id)
        result = await self.session.execute(stmt)
        db_item = result.scalar_one_or_none()
        if db_item:
            return self._to_entity(db_item)
        return None

    async def get_by_id(self, media_id: int) -> Optional[MediaItem]:
        stmt = select(MediaItemDB).where(MediaItemDB.id == media_id)
        result = await self.session.execute(stmt)
        db_item = result.scalar_one_or_none()
        if db_item:
            return self._to_entity(db_item)
        return None

    @staticmethod
    def _to_entity(db: MediaItemDB) -> MediaItem:
        return MediaItem(
            id=db.id,
            external_id=db.external_id,
            title=db.title,
            description=db.description,
            poster_url=db.poster_url,
            rating=db.rating,
            year=db.year,
            director=db.director,
            source=MediaSource(db.source) if db.source else MediaSource.KINOPOISK,
            created_at=db.created_at,
        )

class QueueRepository(IQueueRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_queue(self, chat_id: int, title: str = "Общая очередь") -> Queue:
        db_queue = QueueDB(chat_id=chat_id, title=title)
        self.session.add(db_queue)
        await self.session.flush()
        return Queue(
            id=db_queue.id,
            chat_id=db_queue.chat_id,
            title=db_queue.title,
            created_at=db_queue.created_at,
        )

    async def get_queue_by_chat(self, chat_id: int) -> Optional[Queue]:
        stmt = select(QueueDB).where(QueueDB.chat_id == chat_id)
        result = await self.session.execute(stmt)
        db_q = result.scalar_one_or_none()
        if db_q:
            return Queue(
                id=db_q.id,
                chat_id=db_q.chat_id,
                title=db_q.title,
                created_at=db_q.created_at,
            )
        return None

    async def get_queue_by_id(self, queue_id: int) -> Optional[Queue]:
        stmt = select(QueueDB).where(QueueDB.id == queue_id)
        result = await self.session.execute(stmt)
        db_q = result.scalar_one_or_none()
        if db_q:
            return Queue(
                id=db_q.id,
                chat_id=db_q.chat_id,
                title=db_q.title,
                created_at=db_q.created_at,
            )
        return None

class QueueItemRepository(IQueueItemRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_item(self, item: QueueItem) -> QueueItem:
        db_item = QueueItemDB(
            queue_id=item.queue_id,
            media_id=item.media_id,
            added_by=item.added_by,
            status=item.status.value,
            votes_for=item.votes_for,
            votes_against=item.votes_against,
            message_id=item.message_id,
        )
        self.session.add(db_item)
        await self.session.flush()
        item.id = db_item.id
        return item

    async def get_item(self, item_id: int) -> Optional[QueueItem]:
        stmt = select(QueueItemDB).where(QueueItemDB.id == item_id)
        result = await self.session.execute(stmt)
        db_item = result.scalar_one_or_none()
        if db_item:
            return self._to_entity(db_item)
        return None

    async def update_item(self, item: QueueItem) -> QueueItem:
        await self.session.execute(
            update(QueueItemDB)
            .where(QueueItemDB.id == item.id)
            .values(
                status=item.status.value,
                votes_for=item.votes_for,
                votes_against=item.votes_against,
                message_id=item.message_id,
            )
        )
        return item

    async def get_items_by_queue(self, queue_id: int, status: Optional[str] = None) -> List[QueueItem]:
        stmt = select(QueueItemDB).where(QueueItemDB.queue_id == queue_id)
        if status:
            stmt = stmt.where(QueueItemDB.status == status)
        result = await self.session.execute(stmt)
        return [self._to_entity(i) for i in result.scalars().all()]

    @staticmethod
    def _to_entity(db: QueueItemDB) -> QueueItem:
        return QueueItem(
            id=db.id,
            queue_id=db.queue_id,
            media_id=db.media_id,
            added_by=db.added_by,
            status=QueueItemStatus(db.status),
            votes_for=db.votes_for,
            votes_against=db.votes_against,
            message_id=db.message_id,
            created_at=db.created_at,
        )

class VoteRepository(IVoteRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_vote(self, vote: Vote) -> Vote:
        db_vote = VoteDB(
            queue_item_id=vote.queue_item_id,
            user_id=vote.user_id,
            vote_type=vote.vote_type.value,
        )
        self.session.add(db_vote)
        await self.session.flush()
        vote.id = db_vote.id
        return vote

    async def get_user_vote(self, queue_item_id: int, user_id: int) -> Optional[Vote]:
        stmt = select(VoteDB).where(
            VoteDB.queue_item_id == queue_item_id,
            VoteDB.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        db_v = result.scalar_one_or_none()
        if db_v:
            return Vote(
                id=db_v.id,
                queue_item_id=db_v.queue_item_id,
                user_id=db_v.user_id,
                vote_type=VoteType(db_v.vote_type),
                created_at=db_v.created_at,
            )
        return None

    async def update_vote(self, vote: Vote) -> Vote:
        await self.session.execute(
            update(VoteDB)
            .where(VoteDB.id == vote.id)
            .values(vote_type=vote.vote_type.value)
        )
        return vote

class WatchedHistoryRepository(IWatchedHistoryRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, history: WatchedHistory) -> WatchedHistory:
        db_h = WatchedHistoryDB(
            queue_item_id=history.queue_item_id,
            media_id=history.media_id,
            chat_id=history.chat_id,
            accepted_by=history.accepted_by,
        )
        self.session.add(db_h)
        await self.session.flush()
        history.id = db_h.id
        return history

    async def get_by_chat(self, chat_id: int, limit: int = 10) -> List[WatchedHistory]:
        stmt = select(WatchedHistoryDB).where(WatchedHistoryDB.chat_id == chat_id).order_by(WatchedHistoryDB.accepted_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        db_histories = result.scalars().all()
        return [self._to_entity(h) for h in db_histories]

    @staticmethod
    def _to_entity(db: WatchedHistoryDB) -> WatchedHistory:
        return WatchedHistory(
            id=db.id,
            queue_item_id=db.queue_item_id,
            media_id=db.media_id,
            chat_id=db.chat_id,
            accepted_at=db.accepted_at,
            accepted_by=db.accepted_by,
        )