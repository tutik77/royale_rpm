import logging
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..metrics import collection_run_duration_seconds, decks_collected
from ..models import Card, CollectionRun, Deck, DeckCard
from .clash_api import ClashAPIClient, ClashAPIError

logger = logging.getLogger(__name__)


def _build_signature(card_api_ids: list[int]) -> str:
    return ",".join(str(cid) for cid in sorted(card_api_ids))


def _upsert_card(db: Session, raw: dict) -> Card | None:
    api_id = raw.get("id")
    name = raw.get("name")
    if api_id is None or not name:
        return None

    card = db.query(Card).filter(Card.api_id == api_id).first()
    icon_urls = raw.get("iconUrls") or {}
    rarity = (raw.get("rarity") or "").lower() or None

    if card:
        card.name = name
        card.elixir_cost = raw.get("elixirCost")
        card.max_level = raw.get("maxLevel")
        card.rarity = rarity
        card.icon_url = icon_urls.get("medium") or card.icon_url
    else:
        card = Card(
            api_id=api_id,
            name=name,
            elixir_cost=raw.get("elixirCost"),
            max_level=raw.get("maxLevel"),
            rarity=rarity,
            icon_url=icon_urls.get("medium") or "",
        )
        db.add(card)
        db.flush()

    return card


def _process_player_deck(
    db: Session,
    current_deck: list[dict],
    decks_map: dict[str, dict],
) -> None:
    if len(current_deck) != 8:
        return

    card_api_ids: list[int] = []
    for raw_card in current_deck:
        card = _upsert_card(db, raw_card)
        if card:
            card_api_ids.append(card.api_id)

    if len(card_api_ids) != 8:
        return

    signature = _build_signature(card_api_ids)
    if signature in decks_map:
        decks_map[signature]["count"] += 1
    else:
        decks_map[signature] = {"count": 1, "cards_data": current_deck}


def _persist_decks(
    db: Session, decks_map: dict[str, dict]
) -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    new_decks = 0

    for signature, info in decks_map.items():
        count = info["count"]
        deck = db.query(Deck).filter(Deck.signature == signature).first()

        if deck:
            deck.usage_count += count
            deck.last_seen_at = now
            continue

        card_api_ids = [int(cid) for cid in signature.split(",")]
        cards_db = (
            db.query(Card).filter(Card.api_id.in_(card_api_ids)).all()
        )
        if len(cards_db) != 8:
            continue

        elixir_costs = [c.elixir_cost for c in cards_db if c.elixir_cost]
        avg_elixir = (
            round(sum(elixir_costs) / len(elixir_costs), 1) if elixir_costs else None
        )

        deck = Deck(
            signature=signature,
            avg_elixir=avg_elixir,
            usage_count=count,
            last_seen_at=now,
        )
        db.add(deck)
        db.flush()

        card_by_api_id = {c.api_id: c for c in cards_db}
        for pos, api_id in enumerate(card_api_ids):
            card = card_by_api_id.get(api_id)
            if card:
                db.add(DeckCard(deck_id=deck.id, card_id=card.id, position=pos))

        new_decks += 1

    return len(decks_map), new_decks


def collect_decks(
    db: Session,
    client: ClashAPIClient,
    location_id: str,
    limit: int,
) -> int:
    run = CollectionRun(status="running")
    db.add(run)
    db.commit()
    run_id: int = run.id

    start = time.perf_counter()
    try:
        top_players = client.get_top_players(location_id, limit)
        decks_map: dict[str, dict] = {}
        players_fetched = 0

        for entry in top_players:
            tag = entry.get("tag")
            if not tag:
                continue
            try:
                profile = client.get_player(tag)
                players_fetched += 1
            except ClashAPIError as exc:
                logger.warning("Skipping player %s: %s", tag, exc)
                continue

            current_deck = profile.get("currentDeck", [])
            _process_player_deck(db, current_deck, decks_map)

        db.flush()

        decks_found, new_decks = _persist_decks(db, decks_map)

        run = db.get(CollectionRun, run_id)
        run.players_fetched = players_fetched
        run.decks_found = decks_found
        run.new_decks = new_decks
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

        decks_collected.labels(type="unique").set(decks_found)
        decks_collected.labels(type="new").set(new_decks)

        logger.info(
            "Collection run #%d done: %d players, %d unique decks, %d new",
            run_id, players_fetched, decks_found, new_decks,
        )

    except Exception as exc:
        db.rollback()
        run = db.get(CollectionRun, run_id)
        if run:
            run.status = "failed"
            run.error_message = str(exc)[:2000]
            run.completed_at = datetime.now(timezone.utc)
            db.commit()
        logger.exception("Collection run #%d failed", run_id)
        raise
    finally:
        collection_run_duration_seconds.observe(time.perf_counter() - start)

    return run_id
