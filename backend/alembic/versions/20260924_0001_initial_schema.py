"""Create initial financial schema.

Revision ID: 20260924_0001
Revises:
Create Date: 2026-09-24 00:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260924_0001"
down_revision = None
branch_labels = None
depends_on = None


transaction_type = postgresql.ENUM(
    "DEBIT", "CREDIT", name="transaction_type", create_type=False
)
payment_mode = postgresql.ENUM(
    "UPI",
    "CARD",
    "NEFT",
    "IMPS",
    "RTGS",
    "ATM",
    "CASH",
    "OTHER",
    name="payment_mode",
    create_type=False,
)
transaction_source = postgresql.ENUM(
    "GMAIL",
    "SMS",
    "BANK_STATEMENT",
    "ACCOUNT_AGGREGATOR",
    "MANUAL",
    name="transaction_source",
    create_type=False,
)


def upgrade() -> None:
    """Create normalized users, accounts, categories, and transactions tables."""
    bind = op.get_bind()
    transaction_type.create(bind, checkfirst=True)
    payment_mode.create(bind, checkfirst=True)
    transaction_source.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "financial_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("bank_name", sa.String(length=120), nullable=True),
        sa.Column("account_last4", sa.String(length=4), nullable=True),
        sa.Column("card_last4", sa.String(length=4), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "display_name", name="uq_financial_accounts_user_name"
        ),
    )
    op.create_index("ix_financial_accounts_user_id", "financial_accounts", ["user_id"])
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_categories_user_name"),
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"])
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("transaction_type", transaction_type, nullable=False),
        sa.Column("payment_mode", payment_mode, nullable=False),
        sa.Column("merchant", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("bank_name", sa.String(length=120), nullable=True),
        sa.Column("account_last4", sa.String(length=4), nullable=True),
        sa.Column("card_last4", sa.String(length=4), nullable=True),
        sa.Column("upi_id", sa.String(length=255), nullable=True),
        sa.Column("reference_id", sa.String(length=255), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source", transaction_source, nullable=False),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_transactions_confidence_range",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["financial_accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "fingerprint", name="uq_transactions_user_fingerprint"
        ),
    )
    op.create_index(
        "ix_transactions_user_date", "transactions", ["user_id", "transaction_date"]
    )
    op.create_index(
        "ix_transactions_account_date",
        "transactions",
        ["account_id", "transaction_date"],
    )
    op.create_index(
        "ix_transactions_category_date",
        "transactions",
        ["category_id", "transaction_date"],
    )
    op.create_index(
        "ix_transactions_user_reference_id", "transactions", ["user_id", "reference_id"]
    )
    op.create_index(
        "ix_transactions_user_merchant", "transactions", ["user_id", "merchant"]
    )
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE financial_accounts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE categories ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE transactions ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    """Remove the initial financial schema."""
    op.drop_index("ix_transactions_user_merchant", table_name="transactions")
    op.drop_index("ix_transactions_user_reference_id", table_name="transactions")
    op.drop_index("ix_transactions_category_date", table_name="transactions")
    op.drop_index("ix_transactions_account_date", table_name="transactions")
    op.drop_index("ix_transactions_user_date", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_categories_user_id", table_name="categories")
    op.drop_table("categories")
    op.drop_index("ix_financial_accounts_user_id", table_name="financial_accounts")
    op.drop_table("financial_accounts")
    op.drop_table("users")

    bind = op.get_bind()
    transaction_source.drop(bind, checkfirst=True)
    payment_mode.drop(bind, checkfirst=True)
    transaction_type.drop(bind, checkfirst=True)
