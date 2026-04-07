# Watchlist/celery_app.py
"""
Настройка Celery для проекта Watchlist.
"""

from celery import Celery
from Watchlist.config import settings
from celery.schedules import crontab

# Инициализация Celery с Redis в качестве брокера и бэкенда
celery_app = Celery(
    "watchlist",
    broker="redis://localhost:6379/0",
    backend=settings.REDIS_URL,
    include=["Watchlist.tasks"]
)

# Настройки Celery
celery_app.conf.update(

    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)

celery_app.conf.beat_schedule = {
    "cleanup-votes-daily": {
        "task": "cleanup_old_votes",
        "schedule": crontab(hour=3, minute=0),  # каждый день в 3:00
        "args": (7,),  # удалять голоса старше 7 дней
    },
}

if __name__ == "__main__":
    celery_app.start()