"""Authenticated Gmail connection endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_transaction_service
from app.core.config import get_settings
from app.db.session import get_session
from app.repositories.transactions import TransactionRepository
from app.services.gmail_ingestion import (
    GmailApiClient,
    GmailImportError,
    GmailImportService,
)
from app.services.gmail_oauth import (
    GmailOAuthConfigurationError,
    GmailOAuthStateError,
    build_authorization_request,
    verify_state,
)
from app.services.gmail_sync import GmailSyncService
from app.services.gmail_tokens import GmailTokenCipher, GmailTokenError
from app.services.transactions import TransactionService

router = APIRouter(tags=["gmail"])
ServiceDependency = Annotated[TransactionService, Depends(get_transaction_service)]


@router.get("/gmail/authorize")
def authorize_gmail(account_id: UUID, service: ServiceDependency) -> dict[str, object]:
    """Return a Google consent URL after proving the account belongs to the user."""
    service.ensure_account_owned(account_id)
    try:
        request = build_authorization_request(
            get_settings(), user_id=service.user_id, account_id=account_id
        )
    except GmailOAuthConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gmail connection is not configured",
        ) from error
    return {
        "authorization_url": request.authorization_url,
        "expires_in_seconds": request.expires_in_seconds,
    }


@router.get("/auth/gmail/callback")
def gmail_callback(
    session: Annotated[Session, Depends(get_session)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> dict[str, int | str]:
    """Exchange Google's one-time code and immediately import transaction alerts."""
    settings = get_settings()
    if error or not code or not state or not settings.gmail_oauth_state_secret:
        raise HTTPException(
            status_code=400, detail="Invalid Gmail authorization callback"
        )
    try:
        user_id, account_id = verify_state(settings.gmail_oauth_state_secret, state)
        api = GmailApiClient()
        tokens = api.exchange_code(settings, code)
        repository = TransactionRepository(session)
        if tokens.refresh_token is None:
            raise GmailImportError("Google did not return a refresh token")
        repository.upsert_gmail_connection(
            user_id=user_id,
            account_id=account_id,
            encrypted_refresh_token=GmailTokenCipher(settings).encrypt(
                tokens.refresh_token
            ),
        )
        messages = api.transaction_messages(tokens.access_token)
        result = GmailImportService(repository).import_messages(
            user_id=user_id, account_id=account_id, messages=messages
        )
        connection = repository.get_gmail_connection(user_id, account_id)
        if connection is not None:
            repository.mark_gmail_connection_synced(connection)
    except GmailOAuthStateError as error:
        raise HTTPException(
            status_code=400, detail="Invalid Gmail authorization callback"
        ) from error
    except (GmailImportError, GmailTokenError) as error:
        raise HTTPException(status_code=502, detail="Gmail import failed") from error
    return {
        "status": "completed",
        "scanned": result.scanned,
        "imported": result.imported,
        "duplicates": result.duplicates,
        "unrecognized": result.unrecognized,
    }


@router.post("/gmail/sync")
def sync_gmail(service: ServiceDependency) -> dict[str, int]:
    """Sync connected Gmail accounts belonging only to the authenticated user."""
    try:
        result = GmailSyncService(service.repository, get_settings()).sync_user(
            service.user_id
        )
    except GmailTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gmail synchronization is not configured",
        ) from error
    return {
        "connections": result.connections,
        "imported": result.imported,
        "duplicates": result.duplicates,
        "unrecognized": result.unrecognized,
        "reauthorization_required": result.reauthorization_required,
    }


@router.delete(
    "/gmail/connections/{account_id}", status_code=status.HTTP_204_NO_CONTENT
)
def disconnect_gmail(account_id: UUID, service: ServiceDependency) -> None:
    """Remove encrypted refresh-token material for the caller's account only."""
    connection = service.repository.get_gmail_connection(service.user_id, account_id)
    if connection is not None:
        service.repository.delete_gmail_connection(connection)
