import httpx
from fastapi import FastAPI, HTTPException

from .config import get_settings
from .engine import recommend
from .schemas import (
    DeckIn,
    PlayerCardIn,
    RecommendByTagRequest,
    RecommendRequest,
    RecommendResponse,
)

app = FastAPI(title="Recommendation Service", version="1.0.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/v1/recommend", response_model=RecommendResponse)
def get_recommendations(req: RecommendRequest) -> RecommendResponse:
    """Прямой расчёт — клиент передаёт карты и колоды."""
    return recommend(
        player_cards=req.player_cards,
        decks=req.decks,
        limit=req.limit,
        rating_limit=req.rating_limit,
    )


@app.post("/api/v1/recommend-by-tag", response_model=RecommendResponse)
async def recommend_by_tag(req: RecommendByTagRequest) -> RecommendResponse:
    settings = get_settings()
    tag = req.player_tag.strip()
    if tag.startswith("#"):
        tag = tag[1:]

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            player_resp = await client.get(
                f"{settings.player_service_url}/api/v1/players/{tag}"
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Player Service недоступен: {exc}",
            )
        if player_resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Игрок не найден")
        if player_resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Player Service вернул ошибку: {player_resp.status_code}",
            )

        try:
            decks_resp = await client.get(
                f"{settings.deck_collector_url}/api/v1/decks",
                params={"limit": 200},
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Deck Collector недоступен: {exc}",
            )
        if decks_resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Deck Collector вернул ошибку: {decks_resp.status_code}",
            )

    player_data = player_resp.json()
    decks_data = decks_resp.json().get("items", [])

    player_cards = [PlayerCardIn(**c) for c in player_data.get("cards", [])]
    decks = [DeckIn(**d) for d in decks_data]

    return recommend(
        player_cards=player_cards,
        decks=decks,
        limit=req.limit,
        rating_limit=req.rating_limit,
    )
