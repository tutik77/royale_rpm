from pydantic import BaseModel, ConfigDict


class PlayerCardIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    level: int = 0
    max_level: int | None = None
    rarity: str | None = None
    count: int | None = None


class DeckCardIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    api_id: int
    name: str = ""
    max_level: int | None = None
    icon_url: str = ""


class DeckIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    avg_elixir: float | None = None
    usage_count: int = 0
    cards: list[DeckCardIn]


class RecommendRequest(BaseModel):
    player_cards: list[PlayerCardIn]
    decks: list[DeckIn]
    limit: int = 3
    rating_limit: int = 10


class RecommendByTagRequest(BaseModel):
    player_tag: str
    limit: int = 3
    rating_limit: int = 10


class CardInfo(BaseModel):
    card: dict
    level: int | None = None
    effective_level: int | None = None
    potential_level: int | None = None
    potential_effective_level: int | None = None


class RecommendedDeckOut(BaseModel):
    deck: dict
    owned_cards_count: int
    total_level: int
    total_potential_level: int
    upgradable_cards_count: int
    cards: list[CardInfo]


class RecommendResponse(BaseModel):
    current: list[RecommendedDeckOut]
    potential: list[RecommendedDeckOut]
