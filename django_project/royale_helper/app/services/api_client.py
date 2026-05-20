import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 10


class ServiceUnavailableError(Exception):
    pass


class PlayerNotFoundError(Exception):
    pass


def _get(url: str) -> Any:
    try:
        resp = requests.get(url, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        raise ServiceUnavailableError(f"Service unavailable: {exc}") from exc
    if resp.status_code == 404:
        raise PlayerNotFoundError(resp.json().get("detail", "Not found"))
    if resp.status_code != 200:
        detail = ""
        try:
            detail = resp.json().get("detail", "")
        except Exception:
            detail = resp.text[:200]
        raise ServiceUnavailableError(f"Service error ({resp.status_code}): {detail}")
    return resp.json()


def _post(url: str, json_body: dict) -> Any:
    try:
        resp = requests.post(url, json=json_body, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        raise ServiceUnavailableError(f"Service unavailable: {exc}") from exc
    if resp.status_code != 200:
        detail = ""
        try:
            detail = resp.json().get("detail", "")
        except Exception:
            detail = resp.text[:200]
        raise ServiceUnavailableError(f"Service error ({resp.status_code}): {detail}")
    return resp.json()


def get_player(player_tag: str) -> dict:
    tag = player_tag.strip()
    if tag.startswith("#"):
        tag = tag[1:]
    url = f"{settings.PLAYER_SERVICE_URL}/api/v1/players/{tag}"
    return _get(url)


def get_decks(limit: int = 200) -> list[dict]:
    url = f"{settings.DECK_COLLECTOR_URL}/api/v1/decks?limit={limit}"
    data = _get(url)
    return data.get("items", [])


def get_recommendations(
    player_cards: list[dict],
    decks: list[dict],
    limit: int = 3,
    rating_limit: int = 10,
) -> dict:
    url = f"{settings.RECOMMENDATION_SERVICE_URL}/api/v1/recommend"
    body = {
        "player_cards": player_cards,
        "decks": decks,
        "limit": limit,
        "rating_limit": rating_limit,
    }
    return _post(url, body)


def get_zodiac_card(sign: str) -> dict:
    url = f"{settings.ZODIAC_SERVICE_URL}/api/v1/zodiac?sign={sign}"
    return _get(url)


def get_recommendations_by_tag(
    player_tag: str,
    limit: int = 3,
    rating_limit: int = 10,
) -> dict:
    url = f"{settings.RECOMMENDATION_SERVICE_URL}/api/v1/recommend-by-tag"
    body = {
        "player_tag": player_tag,
        "limit": limit,
        "rating_limit": rating_limit,
    }
    return _post(url, body)
