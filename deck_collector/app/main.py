from fastapi import FastAPI

from .api.routes import router

app = FastAPI(
    title="Clash Royale Deck Collector",
    description="Microservice for collecting and ranking meta decks from top ladder players",
    version="1.0.0",
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
