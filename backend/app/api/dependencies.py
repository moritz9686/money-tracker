"""Authenticated request dependencies."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, SupabaseTokenValidator
from app.core.errors import AuthenticationError
from app.db.session import get_session
from app.repositories.transactions import TransactionRepository
from app.services.transactions import TransactionService

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Missing bearer access token")
    return SupabaseTokenValidator().validate(credentials.credentials)


def get_transaction_service(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> TransactionService:
    return TransactionService(TransactionRepository(session), user.id, user.email)
