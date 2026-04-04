import json
import time
from urllib.parse import quote

import httpx
import redis
from fastapi import FastAPI, HTTPException

from .config import get_settings

app = FastAPI(title="Player Service", version="1.0.0")

_redis: redis.Redis | None = None
_http: httpx.Client | None = None


def _get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.Redis.from_url(
            get_settings().redis_url, decode_responses=True
        )
    return _redis


def _get_http() -> httpx.Client:
    global _http
    if _http is None:
        _http = httpx.Client(timeout=15.0)
    return _http


def _normalize_tag(raw: str) -> str:
    tag = raw.strip().upper().replace("O", "0")
    if tag.startswith("#"):
        tag = tag[1:]
    tag = tag.replace(" ", "")
    allowed = set("0289PYLQGRJCU")
    cleaned = "".join(ch for ch in tag if ch in allowed)
    if not cleaned:
        raise HTTPException(status_code=400, detail="Invalid player tag")
    return f"#{cleaned}"


def _extract_player(data: dict, tag: str) -> dict:
    cards = []
    for c in data.get("cards", []):
        if c.get("id") is None:
            continue
        cards.append({
            "id": c["id"],
            "name": c.get("name", ""),
            "level": c.get("level", 0),
            "max_level": c.get("maxLevel"),
            "star_level": c.get("starLevel"),
            "evolution_level": c.get("evolutionLevel"),
            "rarity": (c.get("rarity") or "").lower(),
            "count": c.get("count"),
            "elixir_cost": c.get("elixirCost"),
            "icon_url": (c.get("iconUrls") or {}).get("medium", ""),
        })
    return {
        "tag": data.get("tag", tag),
        "name": data.get("name", ""),
        "exp_level": data.get("expLevel", 0),
        "trophies": data.get("trophies", 0),
        "best_trophies": data.get("bestTrophies"),
        "cards": cards,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/v1/players/{player_tag:path}")
def get_player(player_tag: str) -> dict:
    settings = get_settings()
    tag = _normalize_tag(player_tag)
    r = _get_redis()

    cache_key = f"player:{tag}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    encoded = quote(tag, safe="")
    url = f"{settings.clash_api_base_url}/players/{encoded}"
    headers = {
        "Authorization": f"Bearer {settings.clash_api_token}",
        "Accept": "application/json",
    }

    resp = _get_http().get(url, headers=headers)

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Игрок с таким тегом не найден.")
    if resp.status_code == 403:
        raise HTTPException(
            status_code=502,
            detail="Доступ к Clash Royale API запрещён. Проверьте токен и IP.",
        )
    if resp.status_code == 429:
        raise HTTPException(status_code=502, detail="API rate limit exceeded.")
    if resp.status_code != 200:
        raise HTTPException(
            status_code=502, detail=f"Clash Royale API error: {resp.status_code}"
        )

    result = _extract_player(resp.json(), tag)
    r.setex(cache_key, settings.player_cache_ttl, json.dumps(result))
    return result
