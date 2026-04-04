from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Card, CollectionRun, Deck
from ..schemas import (
    CardOut,
    CollectResponse,
    CollectionRunOut,
    DeckListResponse,
    DeckOut,
    StatsResponse,
)

router = APIRouter()


def _deck_to_schema(deck: Deck) -> DeckOut:
    cards = [
        CardOut.model_validate(dc.card)
        for dc in sorted(deck.deck_cards, key=lambda dc: dc.position)
    ]
    return DeckOut(
        id=deck.id,
        signature=deck.signature,
        avg_elixir=deck.avg_elixir,
        usage_count=deck.usage_count,
        last_seen_at=deck.last_seen_at,
        created_at=deck.created_at,
        cards=cards,
    )


@router.get("/decks", response_model=DeckListResponse)
def list_decks(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> DeckListResponse:
    total = db.query(Deck).count()
    decks = (
        db.query(Deck)
        .order_by(Deck.usage_count.desc(), Deck.last_seen_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return DeckListResponse(
        items=[_deck_to_schema(d) for d in decks],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/decks/{deck_id}", response_model=DeckOut)
def get_deck(deck_id: int, db: Session = Depends(get_db)) -> DeckOut:
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Deck not found")
    return _deck_to_schema(deck)


@router.get("/cards", response_model=list[CardOut])
def list_cards(db: Session = Depends(get_db)) -> list[CardOut]:
    cards = db.query(Card).order_by(Card.name).all()
    return [CardOut.model_validate(c) for c in cards]


@router.post("/collect", response_model=CollectResponse)
def trigger_collection() -> CollectResponse:
    from ..tasks import collect_top_decks
    task = collect_top_decks.delay()
    return CollectResponse(task_id=task.id, status="dispatched")


@router.delete("/decks")
def purge_decks(db: Session = Depends(get_db)) -> dict:
    from ..models import DeckCard
    deck_count = db.query(Deck).count()
    db.query(DeckCard).delete()
    db.query(Deck).delete()
    db.commit()
    return {"deleted": deck_count}


@router.get("/runs", response_model=list[CollectionRunOut])
def list_runs(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[CollectionRunOut]:
    runs = (
        db.query(CollectionRun)
        .order_by(CollectionRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return [CollectionRunOut.model_validate(r) for r in runs]


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    last_run = (
        db.query(CollectionRun)
        .order_by(CollectionRun.started_at.desc())
        .first()
    )
    return StatsResponse(
        total_decks=db.query(Deck).count(),
        total_cards=db.query(Card).count(),
        total_runs=db.query(CollectionRun).count(),
        last_run=CollectionRunOut.model_validate(last_run) if last_run else None,
    )
