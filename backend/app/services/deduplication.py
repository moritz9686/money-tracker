"""Deterministic transaction deduplication independent of any ingestion source."""

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.db.models import (
    DeduplicationMatchType,
    PaymentMode,
    Transaction,
    TransactionSource,
    TransactionSourceRecord,
    TransactionType,
)

_MERCHANT_NOISE = {
    "PAYMENT",
    "PURCHASE",
    "ORDER",
    "ONLINE",
    "PVT",
    "PRIVATE",
    "LTD",
    "LIMITED",
    "INDIA",
    "UPI",
}
_UNRELIABLE_REFERENCES = {"", "NA", "N/A", "NONE", "UNKNOWN", "NOTAVAILABLE"}


def _normalized_text(value: str | None) -> str:
    if not value:
        return ""
    ascii_value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    )
    return " ".join(re.sub(r"[^A-Z0-9]+", " ", ascii_value.upper()).split())


def normalize_merchant(value: str | None) -> str:
    """Remove common provider-specific merchant formatting noise."""
    return " ".join(
        token
        for token in _normalized_text(value).split()
        if token not in _MERCHANT_NOISE
    )


def normalize_description(value: str | None) -> str:
    """Normalize descriptions for stable fingerprints without raw markup."""
    return _normalized_text(value)


def normalize_reference_id(value: str | None) -> str | None:
    """Return a reliable canonical reference ID, or None for placeholder values."""
    normalized = _normalized_text(value).replace(" ", "")
    if normalized in _UNRELIABLE_REFERENCES or len(normalized) < 6:
        return None
    return normalized


class DeduplicationCandidate(BaseModel):
    """Normalized input from a future source adapter, not an ingestion feature."""

    user_id: UUID
    account_id: UUID
    transaction_date: datetime
    amount: Decimal = Field(gt=Decimal("0"), max_digits=18, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    transaction_type: TransactionType
    payment_mode: PaymentMode
    merchant: str | None = None
    description: str | None = None
    bank_name: str | None = None
    account_last4: str | None = None
    card_last4: str | None = None
    upi_id: str | None = None
    reference_id: str | None = None
    category_id: UUID | None = None
    source: TransactionSource
    confidence: Decimal = Field(default=Decimal("1.000"), ge=0, le=1)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("transaction_date")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("transaction_date must include a timezone")
        return value


@dataclass(frozen=True)
class DeduplicationResult:
    transaction: Transaction
    created: bool
    match_type: DeduplicationMatchType


class TransactionDeduplicationRepository:
    """Persistence protocol implemented by the transaction repository."""

    def find_by_source_fingerprint(
        self, source: TransactionSource, source_fingerprint: str
    ) -> Transaction | None:
        raise NotImplementedError

    def find_by_reference(self, user_id: UUID, reference_id: str) -> Transaction | None:
        raise NotImplementedError

    def find_by_fingerprint(
        self, user_id: UUID, fingerprint: str
    ) -> Transaction | None:
        raise NotImplementedError

    def create_transaction(self, transaction: Transaction) -> Transaction:
        raise NotImplementedError

    def record_source(self, source_record: TransactionSourceRecord) -> None:
        raise NotImplementedError


class TransactionDeduplicationService:
    """Resolve an observation to one logical transaction, preserving provenance."""

    def __init__(self, repository: TransactionDeduplicationRepository) -> None:
        self.repository = repository

    def deduplicate(self, candidate: DeduplicationCandidate) -> DeduplicationResult:
        reference_id = normalize_reference_id(candidate.reference_id)
        logical_fingerprint = self.logical_fingerprint(candidate)
        source_fingerprint = self.source_fingerprint(
            candidate, logical_fingerprint, reference_id
        )

        existing = self.repository.find_by_source_fingerprint(
            candidate.source, source_fingerprint
        )
        if existing:
            return DeduplicationResult(
                existing, created=False, match_type=DeduplicationMatchType.SOURCE
            )

        if reference_id:
            existing = self.repository.find_by_reference(
                candidate.user_id, reference_id
            )
            if existing:
                self._record_source(existing, candidate, source_fingerprint)
                return DeduplicationResult(
                    existing, created=False, match_type=DeduplicationMatchType.REFERENCE
                )

        existing = self.repository.find_by_fingerprint(
            candidate.user_id, logical_fingerprint
        )
        if existing:
            self._record_source(existing, candidate, source_fingerprint)
            return DeduplicationResult(
                existing, created=False, match_type=DeduplicationMatchType.FINGERPRINT
            )

        transaction = self.repository.create_transaction(
            Transaction(
                user_id=candidate.user_id,
                account_id=candidate.account_id,
                transaction_date=candidate.transaction_date,
                amount=candidate.amount,
                currency=candidate.currency,
                transaction_type=candidate.transaction_type,
                payment_mode=candidate.payment_mode,
                merchant=normalize_merchant(candidate.merchant) or None,
                description=normalize_description(candidate.description) or None,
                bank_name=candidate.bank_name,
                account_last4=candidate.account_last4,
                card_last4=candidate.card_last4,
                upi_id=candidate.upi_id,
                reference_id=reference_id,
                category_id=candidate.category_id,
                source=candidate.source,
                confidence=candidate.confidence,
                fingerprint=logical_fingerprint,
            )
        )
        self._record_source(transaction, candidate, source_fingerprint)
        return DeduplicationResult(
            transaction, created=True, match_type=DeduplicationMatchType.NEW
        )

    @staticmethod
    def logical_fingerprint(candidate: DeduplicationCandidate) -> str:
        """Fingerprint stable across source formatting, precise to one minute."""
        timestamp = candidate.transaction_date.astimezone(timezone.utc).replace(
            second=0, microsecond=0
        )
        parts = (
            str(candidate.account_id),
            f"{candidate.amount:.2f}",
            candidate.currency,
            candidate.transaction_type.value,
            candidate.payment_mode.value,
            timestamp.isoformat(),
            normalize_merchant(candidate.merchant),
        )
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    @staticmethod
    def source_fingerprint(
        candidate: DeduplicationCandidate,
        logical_fingerprint: str,
        reference_id: str | None,
    ) -> str:
        """Fingerprint one source observation for idempotent re-imports."""
        parts = (
            candidate.source.value,
            reference_id or logical_fingerprint,
            normalize_description(candidate.description),
        )
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    def _record_source(
        self,
        transaction: Transaction,
        candidate: DeduplicationCandidate,
        source_fingerprint: str,
    ) -> None:
        self.repository.record_source(
            TransactionSourceRecord(
                transaction_id=transaction.id,
                source=candidate.source,
                reference_id=normalize_reference_id(candidate.reference_id),
                source_fingerprint=source_fingerprint,
            )
        )
