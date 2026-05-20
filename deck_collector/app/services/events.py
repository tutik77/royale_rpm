"""Публикация доменных событий в RabbitMQ.

Брокер используется как event bus между микросервисами: deck_collector
выступает producer'ом, объявляет durable topic-exchange и шлёт persistent
JSON-сообщения. Подписчики (например notification_service) биндят свои
очереди к этому exchange по routing key.
"""

import json
import logging
from datetime import datetime, timezone

import pika

from ..config import get_settings

logger = logging.getLogger(__name__)

EXCHANGE = "royale.events"
ROUTING_KEY_COLLECTION_COMPLETED = "decks.collection.completed"


def publish_collection_completed(
    run_id: int,
    decks_found: int,
    new_decks: int,
    players_fetched: int,
) -> None:
    """Опубликовать событие «сбор колод завершён».

    Сбой публикации не должен ронять задачу сбора — логируем и выходим.
    """
    settings = get_settings()
    payload = {
        "event": "decks.collection.completed",
        "run_id": run_id,
        "decks_found": decks_found,
        "new_decks": new_decks,
        "players_fetched": players_fetched,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        params = pika.URLParameters(settings.rabbitmq_url)
        connection = pika.BlockingConnection(params)
        try:
            channel = connection.channel()
            channel.exchange_declare(
                exchange=EXCHANGE, exchange_type="topic", durable=True
            )
            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=ROUTING_KEY_COLLECTION_COMPLETED,
                body=json.dumps(payload).encode("utf-8"),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,  # persistent
                ),
            )
            logger.info(
                "Published %s: run #%d, %d decks (%d new)",
                ROUTING_KEY_COLLECTION_COMPLETED,
                run_id,
                decks_found,
                new_decks,
            )
        finally:
            connection.close()
    except Exception:
        logger.exception("Failed to publish collection event for run #%d", run_id)
