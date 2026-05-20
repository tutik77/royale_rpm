"""Domain models for Clash Royale cards and decks."""

from django.db import models


class Card(models.Model):
    """A single Clash Royale card with metadata from the official API."""

    api_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100)
    max_level = models.PositiveSmallIntegerField(null=True, blank=True)
    max_evolution_level = models.PositiveSmallIntegerField(null=True, blank=True)
    max_star_level = models.PositiveSmallIntegerField(null=True, blank=True)
    icon_url = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Deck(models.Model):
    """A collection of 8 cards representing a playable deck."""

    mode = models.CharField(max_length=50, blank=True)
    avg_elixir = models.FloatField(null=True, blank=True)
    win_rate = models.FloatField(null=True, blank=True)
    avg_crowns = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cards = models.ManyToManyField(Card, through="DeckCard", related_name="decks")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Deck #{self.pk or '—'}"


class DeckCard(models.Model):
    """Through model linking a Card to a Deck with position info."""

    deck = models.ForeignKey(
        Deck,
        on_delete=models.CASCADE,
        related_name="deck_cards",
    )
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE,
        related_name="in_decks",
    )
    position = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["position"]
        unique_together = [("deck", "position")]

    def __str__(self) -> str:
        return f"{self.deck_id}: {self.card} ({self.position})"
