from decimal import Decimal
from pathlib import Path

from sqlalchemy import Numeric

from app.db.base import Base
from app.db.models import Category, FinancialAccount, Transaction, User


def test_initial_schema_registers_all_required_tables() -> None:
    assert {
        "users",
        "financial_accounts",
        "categories",
        "transactions",
        "transaction_source_records",
    }.issubset(Base.metadata.tables)


def test_transaction_uses_exact_numeric_money_and_required_fields() -> None:
    amount_column = Transaction.__table__.c.amount

    assert isinstance(amount_column.type, Numeric)
    assert amount_column.type.precision == 18
    assert amount_column.type.scale == 2
    assert Transaction(amount=Decimal("500.25")).amount == Decimal("500.25")
    assert {
        "id",
        "user_id",
        "account_id",
        "transaction_date",
        "amount",
        "currency",
        "transaction_type",
        "payment_mode",
        "merchant",
        "description",
        "bank_name",
        "account_last4",
        "card_last4",
        "upi_id",
        "reference_id",
        "category_id",
        "source",
        "confidence",
        "fingerprint",
        "created_at",
        "updated_at",
    }.issubset(Transaction.__table__.c.keys())


def test_schema_has_relationships_and_deduplication_constraint() -> None:
    assert User.accounts.property.mapper.class_ is FinancialAccount
    assert FinancialAccount.transactions.property.mapper.class_ is Transaction
    assert Transaction.category.property.mapper.class_ is Category

    constraint_names = {
        constraint.name
        for constraint in Transaction.__table__.constraints
        if constraint.name
    }
    index_names = {index.name for index in Transaction.__table__.indexes}

    assert "uq_transactions_user_fingerprint" in constraint_names
    assert "ix_transactions_user_date" in index_names
    assert "ix_transactions_account_date" in index_names


def test_initial_migration_enables_row_level_security() -> None:
    migration_path = Path("backend/alembic/versions/20260924_0001_initial_schema.py")
    migration_sql = migration_path.read_text()

    for table_name in ("users", "financial_accounts", "categories", "transactions"):
        assert f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY" in migration_sql
