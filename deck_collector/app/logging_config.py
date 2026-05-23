import logging
import sys
from contextvars import ContextVar

from pythonjsonlogger import jsonlogger

SERVICE_NAME = "deck_collector"

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.service = SERVICE_NAME
        return True


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(service)s %(request_id)s %(message)s",
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
            },
        )
    )
    handler.addFilter(ContextFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    for noisy in ("pika", "urllib3"):
        logging.getLogger(noisy).setLevel("WARNING")
