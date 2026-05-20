"""Deck recommendation engine based on player's card collection."""

from dataclasses import dataclass
from typing import Iterable, List

from app.models import Card, Deck

from .clash_royale import PlayerCard, PlayerProfile

CARD_UPGRADE_COSTS_BY_RARITY: dict[str, dict[int, int]] = {
    "common": {
        2: 2, 3: 4, 4: 10, 5: 20, 6: 50, 7: 100,
        8: 200, 9: 400, 10: 800, 11: 1000, 12: 1500, 13: 3000, 14: 5000,
    },
    "rare": {
        3: 1, 4: 2, 5: 4, 6: 10, 7: 20, 8: 50,
        9: 100, 10: 200, 11: 400, 12: 500, 13: 750, 14: 1250,
    },
    "epic": {
        6: 1, 7: 2, 8: 4, 9: 10, 10: 20,
        11: 40, 12: 50, 13: 100, 14: 200,
    },
    "legendary": {
        9: 1, 10: 2, 11: 4, 12: 6, 13: 10, 14: 20,
    },
    "champion": {
        11: 1, 12: 2, 13: 8, 14: 20,
    },
}


@dataclass(frozen=True)
class RecommendedDeckCard:
    """A card in a recommended deck with level info."""

    card: Card
    level: int | None
    effective_level: int | None
    potential_level: int | None
    potential_effective_level: int | None


@dataclass(frozen=True)
class RecommendedDeck:
    """A deck recommendation with scoring metrics."""

    deck: Deck
    owned_cards_count: int
    total_level: int
    total_potential_level: int
    upgradable_cards_count: int
    cards: List[RecommendedDeckCard]


@dataclass(frozen=True)
class DeckRecommendations:
    """Grouped deck recommendations by category."""

    current: List[RecommendedDeck]
    potential: List[RecommendedDeck]


def _effective_level_for_card_level(card: Card, level: int | None) -> int | None:
    """Convert card level to effective level (normalized 1-14 scale)."""
    if level is None:
        return None
    max_level = card.max_level or 0
    if not max_level:
        return level
    return 16 - max_level + level


def _simulate_potential_effective_level(card: PlayerCard) -> int | None:
    """Calculate the max level reachable with available cards."""
    rarity = (card.rarity or "").lower()
    costs = CARD_UPGRADE_COSTS_BY_RARITY.get(rarity)
    if not costs or card.max_level is None:
        return None

    current_effective_level = 16 - card.max_level + card.level
    available_cards = card.count or 0
    level = current_effective_level
    max_effective_level = max(costs.keys())

    while level < max_effective_level:
        next_level = level + 1
        upgrade_cost = costs.get(next_level)
        if upgrade_cost is None or available_cards < upgrade_cost:
            break
        available_cards -= upgrade_cost
        level = next_level

    return level


class DeckRecommender:
    """Scores and ranks decks for a given player profile."""

    def recommend(
        self,
        player: PlayerProfile,
        decks: Iterable[Deck],
        limit: int = 3,
        rating_limit: int = 10,
    ) -> DeckRecommendations:
        """Return ranked deck recommendations for the player."""
        player_cards_by_id = {card.id: card for card in player.cards}
        scored: List[RecommendedDeck] = []

        for deck in decks:
            owned = 0
            total_level = 0
            total_potential_level = 0
            upgradable_cards = 0
            cards: List[RecommendedDeckCard] = []

            for deck_card in deck.deck_cards.all():
                card = deck_card.card
                player_card = player_cards_by_id.get(card.api_id)

                level: int | None = None
                effective_level: int | None = None
                potential_level: int | None = None
                potential_effective_level: int | None = None

                if player_card is not None:
                    owned += 1
                    level = player_card.level
                    effective_level = _effective_level_for_card_level(card, level)
                    potential_effective_level = _simulate_potential_effective_level(
                        player_card
                    )
                    potential_level = potential_effective_level

                    if effective_level is not None:
                        total_level += effective_level
                    if potential_effective_level is not None:
                        total_potential_level += potential_effective_level
                    if (
                        potential_effective_level is not None
                        and effective_level is not None
                        and potential_effective_level > effective_level
                    ):
                        upgradable_cards += 1

                cards.append(
                    RecommendedDeckCard(
                        card=card,
                        level=level,
                        effective_level=effective_level,
                        potential_level=potential_level,
                        potential_effective_level=potential_effective_level,
                    )
                )

            if owned == 0:
                continue

            scored.append(
                RecommendedDeck(
                    deck=deck,
                    owned_cards_count=owned,
                    total_level=total_level,
                    total_potential_level=total_potential_level or total_level,
                    upgradable_cards_count=upgradable_cards,
                    cards=cards,
                )
            )

        current_sorted = sorted(
            scored,
            key=lambda d: (d.owned_cards_count, d.total_level),
            reverse=True,
        )[:limit]

        rating_sorted = sorted(
            scored,
            key=lambda d: (d.total_potential_level, d.total_level),
            reverse=True,
        )[:rating_limit]

        return DeckRecommendations(current=current_sorted, potential=rating_sorted)
