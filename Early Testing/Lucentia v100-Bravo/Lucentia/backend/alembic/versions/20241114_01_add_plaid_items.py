"""add plaid items table and account linkage

Revision ID: b5d1de4d3ebd
Revises: 
Create Date: 2025-11-14 10:25:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "b5d1de4d3ebd"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    if "plaid_items" not in existing_tables:
        op.create_table(
            "plaid_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("item_id", sa.String(), nullable=False),
            sa.Column("access_token", sa.String(), nullable=False),
            sa.Column("institution_name", sa.String(), nullable=True),
            sa.Column("webhook_status", sa.String(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index(
            "ix_plaid_items_item_id", "plaid_items", ["item_id"], unique=True
        )

    account_columns = {col["name"] for col in inspector.get_columns("accounts")}
    if "plaid_item_id" not in account_columns:
        op.add_column(
            "accounts", sa.Column("plaid_item_id", sa.Integer(), nullable=True)
        )
        op.create_foreign_key(
            "fk_accounts_plaid_item_id",
            "accounts",
            "plaid_items",
            ["plaid_item_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    op.drop_constraint(
        "fk_accounts_plaid_item_id", "accounts", type_="foreignkey"
    )
    op.drop_column("accounts", "plaid_item_id")
    op.drop_index("ix_plaid_items_item_id", table_name="plaid_items")
    op.drop_table("plaid_items")
