"""Scope transaction-source deduplication to the authenticated user.

Revision ID: 20260928_0004
Revises: 20260928_0003
Create Date: 2026-09-28 00:00:04
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260928_0004"
down_revision = "20260928_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Prevent duplicates per user without sharing source data across users."""
    # Existing duplicate imports with the same reliable reference are merged
    # before the database constraint is introduced.  Source provenance is
    # retained by moving it to the oldest logical transaction.
    op.execute(
        """
        WITH ranked AS (
            SELECT id, user_id, reference_id,
                   first_value(id) OVER (
                       PARTITION BY user_id, reference_id
                       ORDER BY created_at, id
                   ) AS keep_id,
                   row_number() OVER (
                       PARTITION BY user_id, reference_id
                       ORDER BY created_at, id
                   ) AS row_number
            FROM transactions
            WHERE reference_id IS NOT NULL
        )
        UPDATE transaction_source_records AS records
        SET transaction_id = ranked.keep_id
        FROM ranked
        WHERE records.transaction_id = ranked.id
          AND ranked.row_number > 1
        """
    )
    op.execute(
        """
        WITH ranked AS (
            SELECT id,
                   row_number() OVER (
                       PARTITION BY user_id, reference_id
                       ORDER BY created_at, id
                   ) AS row_number
            FROM transactions
            WHERE reference_id IS NOT NULL
        )
        DELETE FROM transactions
        WHERE id IN (SELECT id FROM ranked WHERE row_number > 1)
        """
    )

    op.add_column(
        "transaction_source_records",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        """
        UPDATE transaction_source_records AS records
        SET user_id = transactions.user_id
        FROM transactions
        WHERE records.transaction_id = transactions.id
        """
    )
    op.alter_column("transaction_source_records", "user_id", nullable=False)
    op.create_foreign_key(
        "fk_transaction_source_records_user_id_users",
        "transaction_source_records",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "uq_transaction_source_records_source_fp",
        "transaction_source_records",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_transaction_source_records_user_source_fp",
        "transaction_source_records",
        ["user_id", "source", "source_fingerprint"],
    )
    op.create_unique_constraint(
        "uq_transactions_user_reference_id",
        "transactions",
        ["user_id", "reference_id"],
    )


def downgrade() -> None:
    """Restore the former source-record uniqueness shape."""
    op.drop_constraint(
        "uq_transactions_user_reference_id", "transactions", type_="unique"
    )
    op.drop_constraint(
        "uq_transaction_source_records_user_source_fp",
        "transaction_source_records",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_transaction_source_records_source_fp",
        "transaction_source_records",
        ["source", "source_fingerprint"],
    )
    op.drop_constraint(
        "fk_transaction_source_records_user_id_users",
        "transaction_source_records",
        type_="foreignkey",
    )
    op.drop_column("transaction_source_records", "user_id")
