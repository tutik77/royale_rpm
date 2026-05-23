"""notification_service — consumer событий из RabbitMQ.

Подписывается на exchange `royale.events` и реагирует на событие
`decks.collection.completed`, которое публикует deck_collector после
завершения сбора меты. Демонстрирует декаплинг сервисов через брокер:
producer и consumer не знают друг о друге, общаются только через очередь.
"""

import json
import logging
import os
import time

import pika

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [notification_service] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE = "royale.events"
QUEUE = "notifications.decks"
ROUTING_KEY = "decks.collection.completed"


def handle_message(channel, method, properties, body: bytes) -> None:
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        logger.warning("Skipping non-JSON message: %r", body)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    logger.info(
        "\U0001F4E2 Мета обновлена: run #%s, найдено %s колод (%s новых), "
        "опрошено %s игроков @ %s",
        event.get("run_id"),
        event.get("decks_found"),
        event.get("new_decks"),
        event.get("players_fetched"),
        event.get("timestamp"),
    )

    # Подтверждаем обработку только после успешной реакции — при падении
    # consumer'а сообщение вернётся в очередь и не потеряется.
    channel.basic_ack(delivery_tag=method.delivery_tag)


def main() -> None:
    params = pika.URLParameters(RABBITMQ_URL)

    # RabbitMQ может стартовать дольше consumer'а — ждём его готовности.
    while True:
        try:
            connection = pika.BlockingConnection(params)
            break
        except pika.exceptions.AMQPConnectionError:
            logger.info("RabbitMQ недоступен, повтор через 3с...")
            time.sleep(3)

    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key=ROUTING_KEY)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE, on_message_callback=handle_message)

    logger.info("Listening on '%s' (key=%s)...", QUEUE, ROUTING_KEY)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
