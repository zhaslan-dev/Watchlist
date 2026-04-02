import redis.asyncio as redis
from Watchlist.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True) if settings.REDIS_URL else None