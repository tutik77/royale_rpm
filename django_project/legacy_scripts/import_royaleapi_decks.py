"""Management command to import popular decks from RoyaleAPI."""

import re
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup  # type: ignore
from django.core.management.base import BaseCommand

from app.models import Card, Deck, DeckCard
from app.services.deck_signature import (
    deck_signature_from_cards,
    deck_signatures_for_queryset,
)

DEFAULT_URL = (
    "https://royaleapi.com/decks/popular"
    "?time=1d&sort=rating&size=30&players=PvP"
    "&min_elixir=1&max_elixir=9&evo=None"
    "&min_cycle_elixir=4&max_cycle_elixir=28"
    "&mode=detail&type=Ranked&global_exclude=false"
)


def parse_decks_from_html(html: str) -> List[Dict[str, Any]]:
    """Parse deck data from RoyaleAPI HTML page."""
    soup = BeautifulSoup(html, "html.parser")
    decks: List[Dict[str, Any]] = []

    for avg_label in soup.find_all(
        string=lambda s: isinstance(s, str) and "Avg Elixir" in s
    ):
        container = avg_label.find_parent("section") or avg_label.find_parent("div")
        if not container:
            continue

        texts = [t.strip() for t in container.stripped_strings if t.strip()]

        try:
            idx = texts.index("Avg Elixir")
        except ValueError:
            continue

        candidates = texts[:idx]

        def looks_like_number(s: str) -> bool:
            return bool(re.fullmatch(r"[0-9]+(\.[0-9]+)?", s.replace(",", ".")))

        bad_tokens = {
            "Deck Stats", "4-Card Cycle", "Rating", "Usage",
            "Wins", "Draws", "Losses",
        }

        filtered: List[str] = []
        for t in candidates:
            if t in bad_tokens or looks_like_number(t) or t.endswith("%"):
                continue
            filtered.append(t)

        seen: set[str] = set()
        cards_reversed: List[str] = []
        for t in reversed(filtered):
            if t in seen:
                continue
            seen.add(t)
            cards_reversed.append(t)
            if len(cards_reversed) == 8:
                break

        if len(cards_reversed) != 8:
            continue

        card_names = list(reversed(cards_reversed))

        avg_elixir = None
        for txt in texts[idx:]:
            if txt == "Avg Elixir":
                continue
            normalized = txt.replace(",", ".").strip()
            try:
                avg_elixir = float(normalized)
                break
            except ValueError:
                continue

        decks.append({"card_names": card_names, "avg_elixir": avg_elixir})

    return decks


class Command(BaseCommand):
    """Import popular decks from RoyaleAPI by scraping their HTML page."""

    help = "Import popular decks from RoyaleAPI into the database."

    def add_arguments(self, parser):
        """Define command-line arguments."""
        parser.add_argument(
            "--url", type=str, default=DEFAULT_URL,
            help="URL of the RoyaleAPI popular decks page.",
        )
        parser.add_argument(
            "--mode", type=str, default="ranked",
            help="Value for Deck.mode field.",
        )

    def handle(self, *args, **options):
        """Execute the deck import process."""
        url = options["url"]
        mode = options["mode"]

        self.stdout.write(f"Downloading RoyaleAPI page: {url}")
        resp = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (royale-helper)",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=25,
        )
        resp.raise_for_status()
        html = resp.text

        markers = ["Best Clash Royale Decks", "Popular Decks", "Deck Stats"]
        if not any(m in html for m in markers):
            self.stdout.write(
                self.style.WARNING(
                    "Expected markers not found in HTML. Page structure may have changed."
                )
            )

        decks_data = parse_decks_from_html(html)
        self.stdout.write(f"Found {len(decks_data)} decks in HTML")

        existing_signatures = deck_signatures_for_queryset(
            Deck.objects.prefetch_related("deck_cards__card").all()
        )

        created_decks = 0
        skipped_decks = 0
        duplicate_decks = 0

        for deck_data in decks_data:
            card_names = deck_data["card_names"]
            cards: List[Card] = []
            missing_card = False

            for name in card_names:
                card = Card.objects.filter(name__iexact=name).first()
                if not card:
                    missing_card = True
                    break
                cards.append(card)

            if missing_card:
                skipped_decks += 1
                continue

            signature = deck_signature_from_cards(cards)
            if signature in existing_signatures:
                duplicate_decks += 1
                continue

            deck = Deck.objects.create(
                mode=mode, avg_elixir=deck_data["avg_elixir"],
                win_rate=None, avg_crowns=None,
            )

            for position, card in enumerate(cards):
                DeckCard.objects.create(deck=deck, card=card, position=position)

            existing_signatures.add(signature)
            created_decks += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created: {created_decks}, "
                f"skipped (missing cards): {skipped_decks}, "
                f"duplicates: {duplicate_decks}."
            )
        )
