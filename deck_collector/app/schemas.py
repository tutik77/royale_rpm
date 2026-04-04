from datetime import datetime

from pydantic import BaseModel


class CardOut(BaseModel):
    model_config = {"from_attributes": True}

    api_id: int
    name: str
    elixir_cost: int | None = None
    max_level: int | None = None
    rarity: str | None = None
    icon_url: str = ""


class DeckOut(BaseModel):
    id: int
    signature: str
    avg_elixir: float | None = None
    usage_count: int = 0
    last_seen_at: datetime | None = None
    created_at: datetime | None = None
    cards: list[CardOut] = []


class DeckListResponse(BaseModel):
    items: list[DeckOut]
    total: int
    limit: int
    offset: int


class CollectionRunOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    players_fetched: int = 0
    decks_found: int = 0
    new_decks: int = 0
    status: str = "pending"
    error_message: str | None = None


class CollectResponse(BaseModel):
    task_id: str
    status: str


class StatsResponse(BaseModel):
    total_decks: int
    total_cards: int
    total_runs: int
    last_run: CollectionRunOut | None = None
