from datetime import datetime

from sqlalchemy import ForeignKey, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    api_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    elixir_cost: Mapped[int | None] = mapped_column(SmallInteger)
    max_level: Mapped[int | None] = mapped_column(SmallInteger)
    rarity: Mapped[str | None] = mapped_column(String(20))
    icon_url: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Card {self.name} ({self.api_id})>"


class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[int] = mapped_column(primary_key=True)
    signature: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    avg_elixir: Mapped[float | None]
    usage_count: Mapped[int] = mapped_column(default=0)
    last_seen_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    deck_cards: Mapped[list["DeckCard"]] = relationship(
        back_populates="deck", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Deck #{self.id} usage={self.usage_count}>"


class DeckCard(Base):
    __tablename__ = "deck_cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    deck_id: Mapped[int] = mapped_column(
        ForeignKey("decks.id", ondelete="CASCADE"), index=True
    )
    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(SmallInteger)

    deck: Mapped["Deck"] = relationship(back_populates="deck_cards")
    card: Mapped["Card"] = relationship(lazy="joined")

    __table_args__ = (UniqueConstraint("deck_id", "position"),)

    def __repr__(self) -> str:
        return f"<DeckCard deck={self.deck_id} pos={self.position}>"


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None]
    players_fetched: Mapped[int] = mapped_column(default=0)
    decks_found: Mapped[int] = mapped_column(default=0)
    new_decks: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error_message: Mapped[str | None] = mapped_column(String(2000))
