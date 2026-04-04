from .schemas import (
    CardInfo,
    DeckCardIn,
    DeckIn,
    PlayerCardIn,
    RecommendedDeckOut,
    RecommendResponse,
)

UPGRADE_COSTS: dict[str, dict[int, int]] = {
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


def _effective_level(max_level: int | None, level: int) -> int | None:
    if max_level is None or max_level == 0:
        return level
    return 16 - max_level + level


def _potential_effective_level(pc: PlayerCardIn) -> int | None:
    rarity = (pc.rarity or "").lower()
    costs = UPGRADE_COSTS.get(rarity)
    if not costs or pc.max_level is None:
        return None

    level = 16 - pc.max_level + pc.level
    available = pc.count or 0
    ceiling = max(costs.keys())

    while level < ceiling:
        cost = costs.get(level + 1)
        if cost is None or available < cost:
            break
        available -= cost
        level += 1

    return level


def _card_dict(dc: DeckCardIn) -> dict:
    return {
        "api_id": dc.api_id,
        "name": dc.name,
        "icon_url": dc.icon_url,
    }


def _deck_dict(deck: DeckIn) -> dict:
    return {
        "id": deck.id,
        "avg_elixir": deck.avg_elixir,
        "usage_count": deck.usage_count,
    }


def recommend(
    player_cards: list[PlayerCardIn],
    decks: list[DeckIn],
    limit: int = 3,
    rating_limit: int = 10,
) -> RecommendResponse:
    by_id = {pc.id: pc for pc in player_cards}
    scored: list[RecommendedDeckOut] = []

    for deck in decks:
        owned = 0
        total_lvl = 0
        total_pot = 0
        upgradable = 0
        cards_out: list[CardInfo] = []

        for dc in deck.cards:
            pc = by_id.get(dc.api_id)
            lvl = None
            eff = None
            pot_lvl = None
            pot_eff = None

            if pc is not None:
                owned += 1
                lvl = pc.level
                eff = _effective_level(dc.max_level or pc.max_level, lvl)
                pot_eff = _potential_effective_level(pc)
                pot_lvl = pot_eff

                if eff is not None:
                    total_lvl += eff
                if pot_eff is not None:
                    total_pot += pot_eff
                if pot_eff and eff and pot_eff > eff:
                    upgradable += 1

            cards_out.append(CardInfo(
                card=_card_dict(dc),
                level=lvl,
                effective_level=eff,
                potential_level=pot_lvl,
                potential_effective_level=pot_eff,
            ))

        if owned == 0:
            continue

        scored.append(RecommendedDeckOut(
            deck=_deck_dict(deck),
            owned_cards_count=owned,
            total_level=total_lvl,
            total_potential_level=total_pot or total_lvl,
            upgradable_cards_count=upgradable,
            cards=cards_out,
        ))

    current = sorted(
        scored, key=lambda d: (d.owned_cards_count, d.total_level), reverse=True
    )[:limit]

    potential = sorted(
        scored, key=lambda d: (d.total_potential_level, d.total_level), reverse=True
    )[:rating_limit]

    return RecommendResponse(current=current, potential=potential)
