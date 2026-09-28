"""One-time Gmail import using transient OAuth access tokens."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx

from app.core.config import Settings
from app.db.models import TransactionSource
from app.repositories.transactions import TransactionRepository
from app.services.deduplication import (
    DeduplicationCandidate,
    TransactionDeduplicationService,
)
from app.services.gmail_parser import parse_transaction_email


class GmailImportError(RuntimeError):
    """Safe Gmail error that never contains email or token content."""


@dataclass(frozen=True)
class GmailImportResult:
    scanned: int
    imported: int
    duplicates: int
    unrecognized: int


@dataclass(frozen=True)
class GoogleAuthorizationTokens:
    access_token: str
    refresh_token: str | None


class GmailApiClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=15.0)

    def exchange_code(self, settings: Settings, code: str) -> GoogleAuthorizationTokens:
        try:
            response = self.client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.gmail_client_id,
                    "client_secret": settings.gmail_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.gmail_redirect_uri,
                },
            )
            response.raise_for_status()
            payload = response.json()
            token = payload.get("access_token")
            if not isinstance(token, str) or not token:
                raise GmailImportError("Google did not return an access token")
            refresh_token = payload.get("refresh_token")
            return GoogleAuthorizationTokens(
                access_token=token,
                refresh_token=refresh_token if isinstance(refresh_token, str) else None,
            )
        except (httpx.HTTPError, ValueError) as error:
            raise GmailImportError("Google authorization failed") from error

    def refresh_access_token(self, settings: Settings, refresh_token: str) -> str:
        try:
            response = self.client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.gmail_client_id,
                    "client_secret": settings.gmail_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            token = response.json().get("access_token")
            if not isinstance(token, str) or not token:
                raise GmailImportError("Google did not return an access token")
            return token
        except (httpx.HTTPError, ValueError) as error:
            raise GmailImportError("Gmail connection needs reauthorization") from error

    def transaction_messages(self, access_token: str) -> list[dict[str, Any]]:
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            listing = self.client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers=headers,
                params={
                    "q": "newer_than:1y {debited credited transaction UPI spent}",
                    "maxResults": 100,
                },
            )
            listing.raise_for_status()
            messages: list[dict[str, Any]] = []
            for item in listing.json().get("messages", []):
                message_id = item.get("id")
                if not isinstance(message_id, str):
                    continue
                detail = self.client.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
                    headers=headers,
                    params={"format": "metadata", "metadataHeaders": "Subject"},
                )
                detail.raise_for_status()
                messages.append(detail.json())
            return messages
        except (httpx.HTTPError, ValueError) as error:
            raise GmailImportError("Gmail messages could not be read") from error


class GmailImportService:
    def __init__(self, repository: TransactionRepository) -> None:
        self.repository = repository
        self.deduplication = TransactionDeduplicationService(repository)

    def import_messages(
        self, *, user_id: UUID, account_id: UUID, messages: list[dict[str, Any]]
    ) -> GmailImportResult:
        if self.repository.get_account(account_id, user_id) is None:
            raise GmailImportError("Financial account was not found")
        imported = duplicates = unrecognized = 0
        for message in messages:
            headers = message.get("payload", {}).get("headers", [])
            subject = next(
                (
                    str(h.get("value", ""))
                    for h in headers
                    if h.get("name") == "Subject"
                ),
                "",
            )
            snippet = str(message.get("snippet", ""))
            try:
                received_at = datetime.fromtimestamp(
                    int(message.get("internalDate", "0")) / 1000, tz=timezone.utc
                )
            except (TypeError, ValueError, OSError):
                unrecognized += 1
                continue
            parsed = parse_transaction_email(
                subject=subject, snippet=snippet, received_at=received_at
            )
            if parsed is None:
                unrecognized += 1
                continue
            safe_description = " ".join(
                part
                for part in (
                    parsed.payment_mode.value,
                    parsed.merchant,
                    parsed.bank_name,
                )
                if part
            )[:500]
            result = self.deduplication.deduplicate(
                DeduplicationCandidate(
                    user_id=user_id,
                    account_id=account_id,
                    transaction_date=parsed.transaction_date,
                    amount=parsed.amount,
                    currency="INR",
                    transaction_type=parsed.transaction_type,
                    payment_mode=parsed.payment_mode,
                    merchant=parsed.merchant,
                    description=safe_description,
                    bank_name=parsed.bank_name,
                    account_last4=parsed.account_last4,
                    card_last4=parsed.card_last4,
                    upi_id=parsed.upi_id,
                    reference_id=parsed.reference_id,
                    source=TransactionSource.GMAIL,
                    confidence=Decimal("0.850"),
                )
            )
            if result.created:
                imported += 1
            else:
                duplicates += 1
        return GmailImportResult(len(messages), imported, duplicates, unrecognized)
