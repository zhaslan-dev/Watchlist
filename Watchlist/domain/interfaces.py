from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import MediaItem, Queue, QueueItem, Vote, VoteType, WatchedHistory

class IMediaRepository(ABC):
    @abstractmethod
    async def add(self, media: MediaItem) -> MediaItem:
        pass
    @abstractmethod
    async def get_by_external_id(self, external_id: str) -> Optional[MediaItem]:
        pass
    @abstractmethod
    async def get_by_id(self, media_id: int) -> Optional[MediaItem]:
        pass

class IQueueRepository(ABC):
    @abstractmethod
    async def create_queue(self, chat_id: int, title: str = "Общая очередь") -> Queue:
        pass
    @abstractmethod
    async def get_queue_by_chat(self, chat_id: int) -> Optional[Queue]:
        pass
    @abstractmethod
    async def get_queue_by_id(self, queue_id: int) -> Optional[Queue]:
        pass

class IQueueItemRepository(ABC):
    @abstractmethod
    async def add_item(self, item: QueueItem) -> QueueItem:
        pass
    @abstractmethod
    async def get_items_by_queue(self, queue_id: int, status: Optional[str] = None) -> List[QueueItem]:
        pass
    @abstractmethod
    async def get_item(self, item_id: int) -> Optional[QueueItem]:
        pass
    @abstractmethod
    async def update_item(self, item: QueueItem) -> QueueItem:
        pass

class IVoteRepository(ABC):
    @abstractmethod
    async def add_vote(self, vote: Vote) -> Vote:
        pass
    @abstractmethod
    async def get_user_vote(self, queue_item_id: int, user_id: int) -> Optional[Vote]:
        pass
    @abstractmethod
    async def update_vote(self, vote: Vote) -> Vote:
        pass

class IWatchedHistoryRepository(ABC):
    @abstractmethod
    async def add(self, history: WatchedHistory) -> WatchedHistory:
        pass
    @abstractmethod
    async def get_by_chat(self, chat_id: int, limit: int = 10) -> List[WatchedHistory]:
        pass