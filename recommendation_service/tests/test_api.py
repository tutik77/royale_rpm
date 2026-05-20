"""API / integration-тесты эндпоинтов.

Прямой /recommend проверяется без сети. /recommend-by-tag оркестрирует
вызовы player_service и deck_collector — внешние HTTP-запросы мокаются
через respx, реальные сервисы не нужны.
"""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PLAYER_URL = "http://player-service:8001/api/v1/players/ABC"
DECKS_URL = "http://collector:8000/api/v1/decks"

PLAYER_PAYLOAD = {
    "tag": "#ABC",
    "cards": [
        {"id": 1, "level": 11, "max_level": 14, "rarity": "common"},
        {"id": 2, "level": 11, "max_level": 14, "rarity": "common"},
    ],
}
DECKS_PAYLOAD = {
    "items": [
        {"id": 10, "cards": [
            {"api_id": 1, "name": "Knight", "max_level": 14},
            {"api_id": 2, "name": "Archers", "max_level": 14},
        ]},
    ]
}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_recommend_direct():
    body = {
        "player_cards": [
            {"id": 1, "level": 11, "max_level": 14, "rarity": "common"},
        ],
        "decks": [
            {"id": 10, "cards": [{"api_id": 1, "name": "Knight", "max_level": 14}]},
        ],
        "limit": 3,
    }
    resp = client.post("/api/v1/recommend", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["current"][0]["deck"]["id"] == 10
    assert data["current"][0]["owned_cards_count"] == 1


@respx.mock
def test_recommend_by_tag_success():
    respx.get(PLAYER_URL).mock(return_value=httpx.Response(200, json=PLAYER_PAYLOAD))
    respx.get(DECKS_URL).mock(return_value=httpx.Response(200, json=DECKS_PAYLOAD))

    resp = client.post("/api/v1/recommend-by-tag", json={"player_tag": "#ABC"})

    assert resp.status_code == 200
    data = resp.json()
    assert "current" in data and "potential" in data
    assert data["current"][0]["deck"]["id"] == 10
    assert data["current"][0]["owned_cards_count"] == 2


@respx.mock
def test_recommend_by_tag_player_not_found():
    respx.get(PLAYER_URL).mock(return_value=httpx.Response(404))

    resp = client.post("/api/v1/recommend-by-tag", json={"player_tag": "ABC"})
    assert resp.status_code == 404


@respx.mock
def test_recommend_by_tag_player_service_down():
    respx.get(PLAYER_URL).mock(side_effect=httpx.ConnectError("refused"))

    resp = client.post("/api/v1/recommend-by-tag", json={"player_tag": "ABC"})
    assert resp.status_code == 503


@respx.mock
def test_recommend_by_tag_deck_collector_error():
    respx.get(PLAYER_URL).mock(return_value=httpx.Response(200, json=PLAYER_PAYLOAD))
    respx.get(DECKS_URL).mock(return_value=httpx.Response(500))

    resp = client.post("/api/v1/recommend-by-tag", json={"player_tag": "ABC"})
    assert resp.status_code == 502
