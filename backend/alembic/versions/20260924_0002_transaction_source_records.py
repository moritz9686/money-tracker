"""Preserve source observations for deduplicated transactions.

Revision ID: 20260924_0002
Revises: 20260924_0001
Create Date: 2026-09-24 00:00:01
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260924_0002"
down_revision = "20260924_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create minimal source provenance storage for logical transactions."""
    op.create_table(
        "transaction_source_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "source",
            postgresql.ENUM(name="transaction_source", create_type=False),
            nullable=False,
        ),
        sa.Column("reference_id", sa.String(length=255), nullable=True),
        sa.Column("source_fingerprint", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"], ["transactions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source",
            "source_fingerprint",
            name="uq_transaction_source_records_source_fp",
        ),
    )
    op.create_index(
        "ix_transaction_source_records_transaction_id",
        "transaction_source_records",
        ["transaction_id"],
    )
    op.create_index(
        "ix_transaction_source_records_reference_id",
        "transaction_source_records",
        ["reference_id"],
    )
    op.execute("ALTER TABLE transaction_source_records ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    """Remove source provenance storage."""
    op.drop_index(
        "ix_transaction_source_records_reference_id",
        table_name="transaction_source_records",
    )
    op.drop_index(
        "ix_transaction_source_records_transaction_id",
        table_name="transaction_source_records",
    )
    op.drop_table("transaction_source_records")
