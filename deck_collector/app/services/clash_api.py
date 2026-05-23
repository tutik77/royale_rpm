import logging
import time
from urllib.parse import quote

import httpx

from ..config import Settings
from ..metrics import clash_api_requests_total

logger = logging.getLogger(__name__)


class ClashAPIError(Exception):
    pass


class ClashAPIClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.clash_api_base_url.rstrip("/")
        self._token = settings.clash_api_token
        self._delay = settings.request_delay
        self._client = httpx.Client(timeout=15.0)
        self._last_request_at = 0.0

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)
        self._last_request_at = time.monotonic()

    def _get(self, path: str, endpoint: str, params: dict | None = None) -> dict:
        self._throttle()
        url = f"{self._base_url}{path}"

        try:
            resp = self._client.get(url, headers=self._headers, params=params)
        except httpx.HTTPError as exc:
            clash_api_requests_total.labels(endpoint=endpoint, status="error").inc()
            raise ClashAPIError(f"Transport error on {endpoint}: {exc}") from exc

        clash_api_requests_total.labels(
            endpoint=endpoint, status=str(resp.status_code)
        ).inc()

        if resp.status_code == 403:
            raise ClashAPIError(
                f"Access forbidden (403). Check API token and IP whitelist. "
                f"Response: {resp.text[:200]}"
            )
        if resp.status_code == 404:
            raise ClashAPIError(f"Not found (404): {path}")
        if resp.status_code == 429:
            raise ClashAPIError("Rate limit exceeded (429). Slow down requests.")
        if resp.status_code != 200:
            raise ClashAPIError(
                f"API error {resp.status_code}: {resp.text[:200]}"
            )

        return resp.json()

    def get_top_players(
        self, location_id: str = "global", limit: int = 200
    ) -> list[dict]:
        data = self._get(
            f"/locations/{location_id}/pathoflegend/players",
            endpoint="top_players",
            params={"limit": limit},
        )
        items = data.get("items", [])
        logger.info("Fetched %d players from Path of Legends (location=%s)", len(items), location_id)
        return items

    def get_player(self, player_tag: str) -> dict:
        if not player_tag.startswith("#"):
            player_tag = f"#{player_tag}"
        encoded = quote(player_tag, safe="")
        return self._get(f"/players/{encoded}", endpoint="player")

    def get_all_cards(self) -> list[dict]:
        data = self._get("/cards", endpoint="cards")
        return data.get("items", [])

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ClashAPIClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
