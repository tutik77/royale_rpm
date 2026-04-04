from celery import Celery

from .config import get_settings

settings = get_settings()

celery = Celery(
    "deck_collector",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "collect-top-decks": {
            "task": "app.tasks.collect_top_decks",
            "schedule": settings.collection_interval_seconds,
        },
    },
)
