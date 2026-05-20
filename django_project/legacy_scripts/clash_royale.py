"""Clash Royale API client for fetching player profiles."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List
from urllib.parse import quote

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class ClashRoyaleAPIError(Exception):
    """Base exception for Clash Royale API errors."""


class PlayerNotFoundError(ClashRoyaleAPIError):
    """Raised when a player tag does not exist."""


@dataclass(frozen=True)
class PlayerCard:
    """A card owned by a player with its current state."""

    id: int
    name: str
    level: int
    max_level: int | None = None
    star_level: int | None = None
    evolution_level: int | None = None
    rarity: str | None = None
    count: int | None = None


@dataclass(frozen=True)
class PlayerProfile:
    """Player account data including owned cards."""

    tag: str
    name: str
    exp_level: int
    trophies: int
    best_trophies: int | None
    cards: List[PlayerCard]


class ClashRoyaleAPI:
    """HTTP client for the official Clash Royale API."""

    def __init__(self, session: requests.Session | None = None) -> None:
        """Initialize the API client with optional custom session."""
        self._session = session or requests.Session()
        self._base_url = getattr(
            settings,
            "CLASH_ROYALE_API_BASE_URL",
            "https://api.clashroyale.com/v1",
        )
        self._token = getattr(settings, "CLASH_ROYALE_API_TOKEN", "")
        if not self._token:
            raise ImproperlyConfigured(
                "CLASH_ROYALE_API_TOKEN не настроен. Добавь его в .env."
            )

    @staticmethod
    def normalize_tag(raw_tag: str) -> str:
        """Clean and validate a player tag string."""
        tag = raw_tag.strip().upper().replace("O", "0")
        if tag.startswith("#"):
            tag = tag[1:]
        tag = tag.replace(" ", "")
        allowed_chars = set("0289PYLQGRJCU")
        cleaned = "".join(ch for ch in tag if ch in allowed_chars)
        if not cleaned:
            raise ValueError("Некорректный тег игрока.")
        return f"#{cleaned}"

    def _headers(self) -> dict[str, str]:
        """Build authorization headers for API requests."""
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    def _save_player_json(self, data: dict) -> None:
        """Save raw API response to disk for debugging."""
        try:
            base_dir = getattr(settings, "BASE_DIR", Path("."))
            output_dir = Path(base_dir) / "player_profiles"
            output_dir.mkdir(parents=True, exist_ok=True)
            tag = (data.get("tag") or "").replace("#", "").replace(" ", "")
            name = data.get("name") or "unknown"
            safe_tag = tag or "unknown"
            filename = f"player_{safe_tag}.json"
            path = output_dir / filename
            payload = {
                "raw": data,
                "meta": {"tag": data.get("tag"), "name": name},
            }
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def get_player(self, raw_tag: str) -> PlayerProfile:
        """Fetch a player profile by tag from the API."""
        normalized_tag = self.normalize_tag(raw_tag)
        encoded_tag = quote(normalized_tag, safe="")
        url = f"{self._base_url}/players/{encoded_tag}"

        response = self._session.get(url, headers=self._headers(), timeout=10)

        if response.status_code == 404:
            raise PlayerNotFoundError("Игрок с таким тегом не найден.")
        if response.status_code == 403:
            raise ClashRoyaleAPIError(
                "Доступ к Clash Royale API запрещён. Проверь токен и whitelist IP."
            )
        if response.status_code != 200:
            raise ClashRoyaleAPIError(
                f"Ошибка Clash Royale API ({response.status_code})."
            )

        data = response.json()
        self._save_player_json(data)

        cards: List[PlayerCard] = []
        for raw_card in data.get("cards") or []:
            card_id = raw_card.get("id")
            if card_id is None:
                continue
            rarity = raw_card.get("rarity")
            rarity_normalized = rarity.lower() if isinstance(rarity, str) else None
            cards.append(
                PlayerCard(
                    id=card_id,
                    name=raw_card.get("name") or "",
                    level=raw_card.get("level") or 0,
                    max_level=raw_card.get("maxLevel"),
                    star_level=raw_card.get("starLevel"),
                    evolution_level=raw_card.get("evolutionLevel"),
                    rarity=rarity_normalized,
                    count=raw_card.get("count"),
                )
            )

        return PlayerProfile(
            tag=data.get("tag") or normalized_tag,
            name=data.get("name") or "",
            exp_level=data.get("expLevel") or 0,
            trophies=data.get("trophies") or 0,
            best_trophies=data.get("bestTrophies"),
            cards=cards,
        )
