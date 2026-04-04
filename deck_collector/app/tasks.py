import logging

from .celery_app import celery
from .config import get_settings
from .database import SessionLocal
from .models import CollectionRun
from .services.clash_api import ClashAPIClient
from .services.collector import collect_decks

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=2)
def collect_top_decks(self):
    settings = get_settings()
    db = SessionLocal()

    try:
        active = (
            db.query(CollectionRun)
            .filter(CollectionRun.status == "running")
            .first()
        )
        if active:
            logger.info("Collection already in progress (run #%d), skipping", active.id)
            return {"status": "skipped", "reason": "already_running"}

        with ClashAPIClient(settings) as client:
            run_id = collect_decks(
                db, client, settings.location_id, settings.top_players_limit,
            )

        return {"run_id": run_id, "status": "completed"}

    except Exception as exc:
        logger.exception("Collection task failed")
        raise self.retry(exc=exc, countdown=120 * (self.request.retries + 1))
    finally:
        db.close()
