"""Safe, format-tolerant parser for synthetic Gmail transaction messages."""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from app.db.models import PaymentMode, TransactionType


@dataclass(frozen=True)
class ParsedGmailTransaction:
    amount: Decimal
    transaction_type: TransactionType
    transaction_date: datetime
    merchant: str | None
    bank_name: str | None
    account_last4: str | None
    card_last4: str | None
    upi_id: str | None
    reference_id: str | None
    payment_mode: PaymentMode
    description: str


_AMOUNT = re.compile(r"(?:₹|INR|Rs\.?)\s*([0-9][0-9,]*(?:\.\d{1,2})?)", re.I)
_LAST4 = re.compile(r"(?:card|account|a/c)\s*(?:ending|xx|x|\*)*\s*(\d{4})", re.I)
_REFERENCE = re.compile(
    r"(?:ref(?:erence)?|utr|rrn|txn(?:\s*id)?)\s*[:#-]?\s*([A-Z0-9-]{6,})", re.I
)
_UPI = re.compile(r"\b([a-z0-9._-]+@[a-z0-9._-]+)\b", re.I)


def is_likely_transaction_email(subject: str, snippet: str) -> bool:
    text = f"{subject} {snippet}".lower()
    return bool(_AMOUNT.search(text)) and any(
        word in text for word in ("debited", "credited", "transaction", "upi", "spent")
    )


def parse_transaction_email(
    *, subject: str, snippet: str, received_at: datetime
) -> ParsedGmailTransaction | None:
    """Return normalized fields or None; never raise for an unknown email."""
    text = " ".join(f"{subject} {snippet}".split())
    if not is_likely_transaction_email(subject, snippet):
        return None
    amount_match = _AMOUNT.search(text)
    if amount_match is None:
        return None
    direction = (
        TransactionType.CREDIT
        if re.search(r"\bcredited\b", text, re.I)
        else TransactionType.DEBIT
    )
    lower = text.lower()
    mode = (
        PaymentMode.UPI
        if "upi" in lower
        else PaymentMode.CARD
        if "card" in lower
        else PaymentMode.OTHER
    )
    last4 = _LAST4.search(text)
    merchant_match = re.search(
        r"(?:at|to|from)\s+([A-Za-z][A-Za-z0-9 .&-]{1,80})", text, re.I
    )
    bank_match = re.search(r"^([A-Za-z][A-Za-z ]{2,40})(?:\s*:|\s+alert)", text)
    reference = _REFERENCE.search(text)
    upi = _UPI.search(text)
    return ParsedGmailTransaction(
        amount=Decimal(amount_match.group(1).replace(",", "")),
        transaction_type=direction,
        transaction_date=received_at
        if received_at.tzinfo
        else received_at.replace(tzinfo=timezone.utc),
        merchant=merchant_match.group(1).strip() if merchant_match else None,
        bank_name=bank_match.group(1).strip() if bank_match else None,
        account_last4=last4.group(1) if last4 else None,
        card_last4=last4.group(1) if mode == PaymentMode.CARD and last4 else None,
        upi_id=upi.group(1) if upi else None,
        reference_id=reference.group(1) if reference else None,
        payment_mode=mode,
        description=text[:500],
    )
