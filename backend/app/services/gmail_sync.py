"""User-initiated and bounded background synchronization for Gmail connections."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.config import Settings
from app.db.models import GmailConnection
from app.repositories.transactions import TransactionRepository
from app.services.gmail_ingestion import (
    GmailApiClient,
    GmailImportError,
    GmailImportResult,
    GmailImportService,
)
from app.services.gmail_tokens import GmailTokenCipher, GmailTokenError


@dataclass(frozen=True)
class GmailSyncResult:
    connections: int
    imported: int
    duplicates: int
    unrecognized: int
    reauthorization_required: int


class GmailSyncService:
    def __init__(self, repository: TransactionRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings
        self.api = GmailApiClient()
        self.cipher = GmailTokenCipher(settings)

    def sync_connection(self, connection: GmailConnection) -> GmailImportResult:
        try:
            refresh_token = self.cipher.decrypt(connection.encrypted_refresh_token)
            access_token = self.api.refresh_access_token(self.settings, refresh_token)
            messages = self.api.transaction_messages(access_token)
            result = GmailImportService(self.repository).import_messages(
                user_id=connection.user_id,
                account_id=connection.account_id,
                messages=messages,
            )
        except (GmailImportError, GmailTokenError):
            self.repository.require_gmail_reauthorization(connection)
            raise
        self.repository.mark_gmail_connection_synced(connection)
        return result

    def sync_user(self, user_id: UUID) -> GmailSyncResult:
        connections = [
            connection
            for account in self.repository.list_accounts(user_id)
            if (connection := self.repository.get_gmail_connection(user_id, account.id))
            and connection.is_active
            and not connection.reauthorization_required
        ]
        return self._sync_connections(connections)

    def sync_due_connections(self) -> GmailSyncResult:
        before = datetime.now(timezone.utc) - timedelta(
            seconds=self.settings.gmail_sync_interval_seconds
        )
        return self._sync_connections(
            self.repository.list_due_gmail_connections(
                before, self.settings.gmail_sync_batch_size
            )
        )

    def _sync_connections(self, connections: list[GmailConnection]) -> GmailSyncResult:
        imported = duplicates = unrecognized = reauthorization_required = 0
        for connection in connections:
            try:
                result = self.sync_connection(connection)
            except (GmailImportError, GmailTokenError):
                reauthorization_required += 1
                continue
            imported += result.imported
            duplicates += result.duplicates
            unrecognized += result.unrecognized
        return GmailSyncResult(
            connections=len(connections),
            imported=imported,
            duplicates=duplicates,
            unrecognized=unrecognized,
            reauthorization_required=reauthorization_required,
        )
