import time
import uuid

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from .api.routes import router
from .logging_config import configure_logging, request_id_var
import logging

configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Clash Royale Deck Collector",
    description="Microservice for collecting and ranking meta decks from top ladder players",
    version="1.0.0",
)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = request_id_var.set(rid)
        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            response.headers["X-Request-ID"] = rid
            logger.info(
                "http_request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            return response
        finally:
            request_id_var.reset(token)


app.add_middleware(RequestContextMiddleware)
app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
