"""Unit tests for the deck recommendation engine."""

from django.test import TestCase

from app.models import Card, Deck, DeckCard
from app.services.clash_royale import PlayerCard, PlayerProfile
from app.services.deck_recommendation import DeckRecommender


class DeckRecommenderTest(TestCase):
    """Tests for DeckRecommender scoring and ranking logic."""

    def setUp(self):
        """Create test cards, decks, and a player profile."""
        cards = []
        for i in range(1, 13):
            cards.append(Card.objects.create(api_id=i, name=f"Card {i}"))

        self.deck_full = Deck.objects.create(mode="test")
        for position, card in enumerate(cards[:8]):
            DeckCard.objects.create(deck=self.deck_full, card=card, position=position)

        self.deck_partial = Deck.objects.create(mode="test")
        for offset, card in enumerate(cards[4:12]):
            DeckCard.objects.create(
                deck=self.deck_partial, card=card, position=offset
            )

        player_cards = [
            PlayerCard(id=i, name=f"Card {i}", level=10) for i in range(1, 9)
        ]

        self.player = PlayerProfile(
            tag="#PLAYER",
            name="Player",
            exp_level=50,
            trophies=7000,
            best_trophies=7500,
            cards=player_cards,
        )

    def test_recommend_prefers_decks_with_more_owned_cards(self):
        """Decks with more owned cards should rank higher."""
        recommender = DeckRecommender()
        decks = Deck.objects.prefetch_related("deck_cards__card").all()

        recommendations = recommender.recommend(self.player, decks, limit=3)

        self.assertTrue(recommendations.current)
        self.assertEqual(recommendations.current[0].deck, self.deck_full)
        self.assertGreater(
            recommendations.current[0].owned_cards_count,
            recommendations.current[1].owned_cards_count,
        )
