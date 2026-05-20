"""Utilities for generating unique deck signatures."""

from typing import Iterable, Set

from app.models import Card, Deck


def deck_signature_from_cards(cards: Iterable[Card]) -> str:
    """Generate a unique signature string from a list of cards."""
    api_ids = sorted({card.api_id for card in cards})
    return ",".join(str(api_id) for api_id in api_ids)


def deck_signatures_for_queryset(decks: Iterable[Deck]) -> Set[str]:
    """Build a set of signatures for all decks in a queryset."""
    signatures: Set[str] = set()
    for deck in decks:
        cards = [deck_card.card for deck_card in deck.deck_cards.all()]
        signatures.add(deck_signature_from_cards(cards))
    return signatures
