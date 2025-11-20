"""add plaid item sync tracking

Revision ID: f2f3b7cc58d9
Revises: b5d1de4d3ebd
Create Date: 2025-11-15 15:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f2f3b7cc58d9"
down_revision = "b5d1de4d3ebd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "plaid_items",
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "plaid_sync_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plaid_item_id", sa.Integer(), nullable=False),
        sa.Column(
            "event_type",
            sa.String(length=50),
            nullable=False,
            server_default="exchange",
        ),
        sa.Column(
            "transactions_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "pages_fetched",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["plaid_item_id"],
            ["plaid_items.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_plaid_sync_events_item_created",
        "plaid_sync_events",
        ["plaid_item_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_plaid_sync_events_item_created", table_name="plaid_sync_events")
    op.drop_table("plaid_sync_events")
    op.drop_column("plaid_items", "last_synced_at")
