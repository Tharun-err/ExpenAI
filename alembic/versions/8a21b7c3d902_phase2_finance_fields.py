
"""Add transaction dates, external IDs and budgets.

Revision ID: 8a21b7c3d902
Revises: 50cd9ec42164
"""

from alembic import op
import sqlalchemy as sa


revision = "8a21b7c3d902"
down_revision = "50cd9ec42164"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("transaction_date", sa.Date(), nullable=True),
    )

    op.execute(
        """
        UPDATE transactions
        SET transaction_date = CAST(created_at AS DATE)
        WHERE transaction_date IS NULL
        """
    )

    op.alter_column(
        "transactions",
        "transaction_date",
        existing_type=sa.Date(),
        nullable=False,
        server_default=sa.text("CURRENT_DATE"),
    )

    op.add_column(
        "transactions",
        sa.Column("external_id", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.CheckConstraint(
            "amount > 0",
            name="ck_budget_amount_positive",
        ),
    )

    op.create_index(
        "ix_budgets_id",
        "budgets",
        ["id"],
        unique=False,
    )

    op.create_unique_constraint(
        "uq_transaction_account_external_id",
        "transactions",
        ["account_id", "external_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_transaction_account_external_id",
        "transactions",
        type_="unique",
    )
    op.drop_index("ix_budgets_id", table_name="budgets")
    op.drop_table("budgets")
    op.drop_column("transactions", "external_id")
    op.drop_column("transactions", "transaction_date")
