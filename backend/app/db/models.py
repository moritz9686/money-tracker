"""Initial source-independent financial data schema.

These models define storage only. Parsing, ingestion, categorization, and
deduplication workflows are deliberately outside this milestone.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TransactionType(str, Enum):
    """Direction of money movement."""

    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class PaymentMode(str, Enum):
    """Normalized way a transaction was made."""

    UPI = "UPI"
    CARD = "CARD"
    NEFT = "NEFT"
    IMPS = "IMPS"
    RTGS = "RTGS"
    ATM = "ATM"
    CASH = "CASH"
    OTHER = "OTHER"


class TransactionSource(str, Enum):
    """Source that supplied a normalized transaction."""

    GMAIL = "GMAIL"
    SMS = "SMS"
    BANK_STATEMENT = "BANK_STATEMENT"
    ACCOUNT_AGGREGATOR = "ACCOUNT_AGGREGATOR"
    MANUAL = "MANUAL"


class DeduplicationMatchType(str, Enum):
    """Reason an incoming observation resolved to an existing transaction."""

    SOURCE = "SOURCE"
    REFERENCE = "REFERENCE"
    FINGERPRINT = "FINGERPRINT"
    NEW = "NEW"


class User(Base):
    """Application user, intentionally without authentication implementation."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    accounts: Mapped[list["FinancialAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    categories: Mapped[list["Category"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class FinancialAccount(Base):
    """A bank account, card, or other financial account belonging to one user."""

    __tablename__ = "financial_accounts"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "display_name", name="uq_financial_accounts_user_name"
        ),
        Index("ix_financial_accounts_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(120))
    account_last4: Mapped[str | None] = mapped_column(String(4))
    card_last4: Mapped[str | None] = mapped_column(String(4))
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")


class Category(Base):
    """System or user-owned transaction category."""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_categories_user_name"),
        Index("ix_categories_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User | None] = relationship(back_populates="categories")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")


class Transaction(Base):
    """Normalized logical financial transaction without source-ingestion logic."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_transactions_confidence_range",
        ),
        UniqueConstraint(
            "user_id", "fingerprint", name="uq_transactions_user_fingerprint"
        ),
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_account_date", "account_id", "transaction_date"),
        Index("ix_transactions_category_date", "category_id", "transaction_date"),
        Index("ix_transactions_user_reference_id", "user_id", "reference_id"),
        Index("ix_transactions_user_merchant", "user_id", "merchant"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("financial_accounts.id", ondelete="RESTRICT"), nullable=False
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        SqlEnum(TransactionType, name="transaction_type"), nullable=False
    )
    payment_mode: Mapped[PaymentMode] = mapped_column(
        SqlEnum(PaymentMode, name="payment_mode"), nullable=False
    )
    merchant: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    bank_name: Mapped[str | None] = mapped_column(String(120))
    account_last4: Mapped[str | None] = mapped_column(String(4))
    card_last4: Mapped[str | None] = mapped_column(String(4))
    upi_id: Mapped[str | None] = mapped_column(String(255))
    reference_id: Mapped[str | None] = mapped_column(String(255))
    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL")
    )
    source: Mapped[TransactionSource] = mapped_column(
        SqlEnum(TransactionSource, name="transaction_source"), nullable=False
    )
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), default=Decimal("1.000"), nullable=False
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="transactions")
    account: Mapped[FinancialAccount] = relationship(back_populates="transactions")
    category: Mapped[Category | None] = relationship(back_populates="transactions")
    source_records: Mapped[list["TransactionSourceRecord"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )


class TransactionSourceRecord(Base):
    """Minimal provenance record for an observation mapped to one transaction."""

    __tablename__ = "transaction_source_records"
    __table_args__ = (
        UniqueConstraint(
            "source",
            "source_fingerprint",
            name="uq_transaction_source_records_source_fp",
        ),
        Index("ix_transaction_source_records_transaction_id", "transaction_id"),
        Index("ix_transaction_source_records_reference_id", "reference_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[TransactionSource] = mapped_column(
        SqlEnum(TransactionSource, name="transaction_source", create_type=False),
        nullable=False,
    )
    reference_id: Mapped[str | None] = mapped_column(String(255))
    source_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    transaction: Mapped[Transaction] = relationship(back_populates="source_records")
