"""Typed API contracts for transaction operations."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db.models import PaymentMode, TransactionSource, TransactionType

Money = Annotated[Decimal, Field(gt=Decimal("0"), max_digits=18, decimal_places=2)]
Confidence = Annotated[
    Decimal, Field(ge=Decimal("0"), le=Decimal("1"), max_digits=4, decimal_places=3)
]


class TransactionCreate(BaseModel):
    account_id: UUID
    transaction_date: datetime
    amount: Money
    currency: Annotated[str, Field(min_length=3, max_length=3)] = "INR"
    transaction_type: TransactionType
    payment_mode: PaymentMode
    merchant: Annotated[str | None, Field(max_length=255)] = None
    description: str | None = None
    bank_name: Annotated[str | None, Field(max_length=120)] = None
    account_last4: Annotated[str | None, Field(pattern=r"^\d{4}$")] = None
    card_last4: Annotated[str | None, Field(pattern=r"^\d{4}$")] = None
    upi_id: Annotated[str | None, Field(max_length=255)] = None
    reference_id: Annotated[str | None, Field(max_length=255)] = None
    category_id: UUID | None = None
    source: TransactionSource
    confidence: Confidence = Decimal("1.000")
    fingerprint: Annotated[str, Field(min_length=1, max_length=64)]

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class TransactionUpdate(BaseModel):
    account_id: UUID | None = None
    transaction_date: datetime | None = None
    amount: Money | None = None
    currency: Annotated[str | None, Field(min_length=3, max_length=3)] = None
    transaction_type: TransactionType | None = None
    payment_mode: PaymentMode | None = None
    merchant: Annotated[str | None, Field(max_length=255)] = None
    description: str | None = None
    bank_name: Annotated[str | None, Field(max_length=120)] = None
    account_last4: Annotated[str | None, Field(pattern=r"^\d{4}$")] = None
    card_last4: Annotated[str | None, Field(pattern=r"^\d{4}$")] = None
    upi_id: Annotated[str | None, Field(max_length=255)] = None
    reference_id: Annotated[str | None, Field(max_length=255)] = None
    category_id: UUID | None = None
    source: TransactionSource | None = None
    confidence: Confidence | None = None
    fingerprint: Annotated[str | None, Field(min_length=1, max_length=64)] = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @model_validator(mode="after")
    def require_at_least_one_update(self) -> "TransactionUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be supplied")
        required_fields = (
            "account_id",
            "transaction_date",
            "amount",
            "currency",
            "transaction_type",
            "payment_mode",
            "source",
            "confidence",
            "fingerprint",
        )
        for field_name in required_fields:
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                raise ValueError(f"{field_name} cannot be null")
        return self


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    account_id: UUID
    transaction_date: datetime
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    payment_mode: PaymentMode
    merchant: str | None
    description: str | None
    bank_name: str | None
    account_last4: str | None
    card_last4: str | None
    upi_id: str | None
    reference_id: str | None
    category_id: UUID | None
    source: TransactionSource
    confidence: Decimal
    fingerprint: str
    created_at: datetime
    updated_at: datetime


class TransactionPage(BaseModel):
    items: list[TransactionRead]
    total: int
    limit: int
    offset: int


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    detail: ErrorDetail
