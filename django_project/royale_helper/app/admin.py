"""Django admin configuration for Royale Helper models."""

from django.contrib import admin

from .models import Card, Deck, DeckCard


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    """Admin interface for Card model."""

    list_display = ("name", "api_id", "max_level")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    """Admin interface for Deck model."""

    list_display = ("id", "mode", "avg_elixir", "win_rate", "created_at")
    list_filter = ("mode",)
    ordering = ("-created_at",)


@admin.register(DeckCard)
class DeckCardAdmin(admin.ModelAdmin):
    """Admin interface for DeckCard through model."""

    list_display = ("deck", "card", "position")
    list_filter = ("deck",)
    ordering = ("deck", "position")
