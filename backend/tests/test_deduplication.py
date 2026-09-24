from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.db.models import (
    DeduplicationMatchType,
    PaymentMode,
    Transaction,
    TransactionSource,
    TransactionSourceRecord,
    TransactionType,
)
from app.services.deduplication import (
    DeduplicationCandidate,
    TransactionDeduplicationService,
    normalize_description,
    normalize_merchant,
)

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
ACCOUNT_ID = UUID("00000000-0000-0000-0000-000000000010")
TRANSACTION_TIME = datetime(2026, 9, 24, 12, 30, 45, tzinfo=timezone.utc)


class InMemoryDeduplicationRepository:
    def __init__(self) -> None:
        self.transactions: list[Transaction] = []
        self.source_records: list[TransactionSourceRecord] = []

    def find_by_source_fingerprint(
        self, source: TransactionSource, source_fingerprint: str
    ) -> Transaction | None:
        for record in self.source_records:
            if (
                record.source == source
                and record.source_fingerprint == source_fingerprint
            ):
                return next(
                    item
                    for item in self.transactions
                    if item.id == record.transaction_id
                )
        return None

    def find_by_reference(self, user_id: UUID, reference_id: str) -> Transaction | None:
        for transaction in self.transactions:
            if (
                transaction.user_id == user_id
                and transaction.reference_id == reference_id
            ):
                return transaction
        for record in self.source_records:
            if record.reference_id == reference_id:
                transaction = next(
                    item
                    for item in self.transactions
                    if item.id == record.transaction_id
                )
                if transaction.user_id == user_id:
                    return transaction
        return None

    def find_by_fingerprint(
        self, user_id: UUID, fingerprint: str
    ) -> Transaction | None:
        return next(
            (
                transaction
                for transaction in self.transactions
                if transaction.user_id == user_id
                and transaction.fingerprint == fingerprint
            ),
            None,
        )

    def create_transaction(self, transaction: Transaction) -> Transaction:
        transaction.id = uuid4()
        self.transactions.append(transaction)
        return transaction

    def record_source(self, source_record: TransactionSourceRecord) -> None:
        self.source_records.append(source_record)


def candidate(**overrides: object) -> DeduplicationCandidate:
    values: dict[str, object] = {
        "user_id": USER_ID,
        "account_id": ACCOUNT_ID,
        "transaction_date": TRANSACTION_TIME,
        "amount": Decimal("500.00"),
        "currency": "INR",
        "transaction_type": TransactionType.DEBIT,
        "payment_mode": PaymentMode.UPI,
        "merchant": "Swiggy",
        "description": "UPI payment to Swiggy",
        "source": TransactionSource.SMS,
        "confidence": Decimal("0.950"),
    }
    values.update(overrides)
    return DeduplicationCandidate(**values)


def test_exact_source_import_is_idempotent() -> None:
    repository = InMemoryDeduplicationRepository()
    service = TransactionDeduplicationService(repository)

    first = service.deduplicate(candidate(reference_id="UPI-REF-123456"))
    second = service.deduplicate(candidate(reference_id="UPI-REF-123456"))

    assert first.created is True
    assert second.created is False
    assert second.match_type is DeduplicationMatchType.SOURCE
    assert len(repository.transactions) == 1
    assert len(repository.source_records) == 1


def test_cross_source_reference_id_resolves_to_one_logical_transaction() -> None:
    repository = InMemoryDeduplicationRepository()
    service = TransactionDeduplicationService(repository)

    first = service.deduplicate(candidate(reference_id="UPI-REF-123456"))
    second = service.deduplicate(
        candidate(
            source=TransactionSource.GMAIL,
            merchant="SWIGGY PVT. LTD.",
            description="Your UPI transaction at Swiggy",
            reference_id="upi ref 123456",
        )
    )

    assert second.created is False
    assert second.match_type is DeduplicationMatchType.REFERENCE
    assert second.transaction.id == first.transaction.id
    assert len(repository.source_records) == 2


def test_same_amount_with_different_merchants_is_not_deduplicated() -> None:
    repository = InMemoryDeduplicationRepository()
    service = TransactionDeduplicationService(repository)

    service.deduplicate(candidate(merchant="Swiggy"))
    result = service.deduplicate(
        candidate(source=TransactionSource.GMAIL, merchant="Zomato")
    )

    assert result.created is True
    assert len(repository.transactions) == 2


def test_missing_reference_id_uses_normalized_fingerprint_across_sources() -> None:
    repository = InMemoryDeduplicationRepository()
    service = TransactionDeduplicationService(repository)

    first = service.deduplicate(candidate(reference_id=None))
    second = service.deduplicate(
        candidate(
            source=TransactionSource.BANK_STATEMENT,
            merchant="SWIGGY*ORDER",
            description="upi-payment / swiggy",
            reference_id=None,
        )
    )

    assert second.created is False
    assert second.match_type is DeduplicationMatchType.FINGERPRINT
    assert second.transaction.id == first.transaction.id


def test_merchant_and_description_normalization_handles_formatting_differences() -> (
    None
):
    assert normalize_merchant("Swiggy Pvt. Ltd. UPI") == "SWIGGY"
    assert normalize_description(" UPI-payment / Swiggy ") == "UPI PAYMENT SWIGGY"


def test_similar_transactions_two_minutes_apart_are_not_deduplicated() -> None:
    repository = InMemoryDeduplicationRepository()
    service = TransactionDeduplicationService(repository)

    service.deduplicate(candidate(reference_id=None))
    later = service.deduplicate(
        candidate(
            source=TransactionSource.GMAIL,
            reference_id=None,
            transaction_date=TRANSACTION_TIME + timedelta(minutes=2),
        )
    )

    assert later.created is True
    assert len(repository.transactions) == 2
