"""Юнит-тесты движка рекомендаций — чистая логика без сети и БД."""

import pytest

from app.engine import (
    _effective_level,
    _potential_effective_level,
    recommend,
)
from app.schemas import DeckCardIn, DeckIn, PlayerCardIn


# --- _effective_level ---------------------------------------------------

@pytest.mark.parametrize(
    "max_level, level, expected",
    [
        (None, 5, 5),     # нет max_level — уровень как есть
        (0, 7, 7),        # max_level == 0 трактуется как «нет данных»
        (14, 14, 16),     # обычная карта на максимуме нормализуется к 16
        (14, 11, 13),     # 16 - 14 + 11
        (13, 11, 14),     # карта с другим max_level
    ],
)
def test_effective_level(max_level, level, expected):
    assert _effective_level(max_level, level) == expected


# --- _potential_effective_level ----------------------------------------

def test_potential_none_without_rarity():
    pc = PlayerCardIn(id=1, level=5, max_level=14, rarity=None, count=9999)
    assert _potential_effective_level(pc) is None


def test_potential_none_without_max_level():
    pc = PlayerCardIn(id=1, level=5, max_level=None, rarity="common", count=9999)
    assert _potential_effective_level(pc) is None


def test_potential_no_currency_returns_current_effective():
    # common, max_level 14, game-level 1 -> effective 16-14+1 = 3, без карт не растёт
    pc = PlayerCardIn(id=1, level=1, max_level=14, rarity="common", count=0)
    assert _potential_effective_level(pc) == 3


def test_potential_upgrades_one_level_with_enough_cards():
    # effective 3, апгрейд до 4 стоит 10 common-карт — ровно хватает на +1
    pc = PlayerCardIn(id=1, level=1, max_level=14, rarity="common", count=10)
    assert _potential_effective_level(pc) == 4


# --- recommend ----------------------------------------------------------

def _common(card_id: int, level: int) -> PlayerCardIn:
    return PlayerCardIn(id=card_id, level=level, max_level=14, rarity="common", count=0)


def _deck(deck_id: int, *api_ids: int) -> DeckIn:
    return DeckIn(
        id=deck_id,
        cards=[DeckCardIn(api_id=a, name=f"card{a}", max_level=14) for a in api_ids],
    )


def test_recommend_skips_decks_with_no_owned_cards():
    player = [_common(1, 11), _common(2, 11)]
    decks = [
        _deck(10, 1, 2),    # owned 2
        _deck(20, 1, 99),   # owned 1
        _deck(30, 98, 99),  # owned 0 -> отсеивается
    ]
    res = recommend(player, decks)

    ids = {d.deck["id"] for d in res.current}
    assert 30 not in ids
    assert ids == {10, 20}


def test_recommend_orders_by_owned_then_level():
    player = [_common(1, 11), _common(2, 11)]
    decks = [_deck(20, 1, 99), _deck(10, 1, 2)]
    res = recommend(player, decks)

    # больше своих карт -> выше
    assert res.current[0].deck["id"] == 10
    assert res.current[0].owned_cards_count == 2
    assert res.current[0].total_level == 26  # 13 + 13
    assert res.current[1].deck["id"] == 20
    assert res.current[1].owned_cards_count == 1


def test_recommend_respects_limit():
    player = [_common(1, 11), _common(2, 11)]
    decks = [_deck(10, 1, 2), _deck(20, 1, 99)]
    res = recommend(player, decks, limit=1)
    assert len(res.current) == 1


def test_recommend_counts_upgradable_cards():
    # карта с запасом для апгрейда -> upgradable_cards_count > 0
    player = [PlayerCardIn(id=1, level=1, max_level=14, rarity="common", count=10)]
    res = recommend(player, [_deck(10, 1)])
    assert res.current[0].upgradable_cards_count == 1


def test_recommend_empty_when_no_decks():
    res = recommend([_common(1, 11)], [])
    assert res.current == []
    assert res.potential == []
