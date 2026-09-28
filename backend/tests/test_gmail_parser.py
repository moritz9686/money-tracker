from datetime import datetime, timezone
from decimal import Decimal

from app.db.models import PaymentMode, TransactionType
from app.services.gmail_parser import (
    is_likely_transaction_email,
    parse_transaction_email,
)


def test_parses_synthetic_upi_debit_email() -> None:
    parsed = parse_transaction_email(
        subject="HDFC Bank: UPI transaction alert",
        snippet=(
            "Rs. 500.25 debited from account ending 1234 to Swiggy. "
            "UTR: ABCD123456. user@upi"
        ),
        received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert parsed is not None
    assert parsed.amount == Decimal("500.25")
    assert parsed.transaction_type == TransactionType.DEBIT
    assert parsed.payment_mode == PaymentMode.UPI
    assert parsed.reference_id == "ABCD123456"


def test_recognizes_known_merchant_in_varied_email_format() -> None:
    parsed = parse_transaction_email(
        subject="Payment received",
        snippet="Your card was debited INR 499.00 for SWIGGY order. Ref TEST123456",
        received_at=datetime(2026, 9, 28, tzinfo=timezone.utc),
    )

    assert parsed is not None
    assert parsed.merchant == "Swiggy"


def test_ignores_unrelated_synthetic_email() -> None:
    assert not is_likely_transaction_email("Welcome", "Your account is ready")
    assert (
        parse_transaction_email(
            subject="Welcome",
            snippet="Your account is ready",
            received_at=datetime.now(timezone.utc),
        )
        is None
    )
