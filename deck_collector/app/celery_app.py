from celery import Celery
from celery.signals import task_postrun, task_prerun, worker_ready
from prometheus_client import start_http_server

from .config import get_settings
from .logging_config import configure_logging, request_id_var
from .metrics import METRICS_PORT

configure_logging()

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
    worker_hijack_root_logger=False,
    beat_schedule={
        "collect-top-decks": {
            "task": "app.tasks.collect_top_decks",
            "schedule": settings.collection_interval_seconds,
        },
    },
)

_task_tokens: dict[str, object] = {}


@worker_ready.connect
def _start_metrics_server(**_: object) -> None:
    start_http_server(METRICS_PORT)


@task_prerun.connect
def _bind_request_id(task_id: str, **_: object) -> None:
    _task_tokens[task_id] = request_id_var.set(task_id)


@task_postrun.connect
def _unbind_request_id(task_id: str, **_: object) -> None:
    token = _task_tokens.pop(task_id, None)
    if token is not None:
        request_id_var.reset(token)
