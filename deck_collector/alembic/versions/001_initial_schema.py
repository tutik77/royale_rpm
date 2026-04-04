"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("api_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("elixir_cost", sa.SmallInteger(), nullable=True),
        sa.Column("rarity", sa.String(20), nullable=True),
        sa.Column("icon_url", sa.String(500), server_default=""),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("api_id"),
    )
    op.create_index("ix_cards_api_id", "cards", ["api_id"])

    op.create_table(
        "decks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("signature", sa.String(200), nullable=False),
        sa.Column("avg_elixir", sa.Float(), nullable=True),
        sa.Column("usage_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("signature"),
    )
    op.create_index("ix_decks_signature", "decks", ["signature"])

    op.create_table(
        "deck_cards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "deck_id",
            sa.Integer(),
            sa.ForeignKey("decks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "card_id",
            sa.Integer(),
            sa.ForeignKey("cards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.UniqueConstraint("deck_id", "position"),
    )
    op.create_index("ix_deck_cards_deck_id", "deck_cards", ["deck_id"])
    op.create_index("ix_deck_cards_card_id", "deck_cards", ["card_id"])

    op.create_table(
        "collection_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("players_fetched", sa.Integer(), server_default="0"),
        sa.Column("decks_found", sa.Integer(), server_default="0"),
        sa.Column("new_decks", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(20), server_default="'pending'"),
        sa.Column("error_message", sa.String(2000), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("collection_runs")
    op.drop_table("deck_cards")
    op.drop_table("decks")
    op.drop_table("cards")
