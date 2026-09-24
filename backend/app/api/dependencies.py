"""Temporary, isolated development-user dependency."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.repositories.transactions import TransactionRepository
from app.services.transactions import TransactionService

DEFAULT_DEVELOPMENT_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def get_development_user_id(
    x_development_user_id: Annotated[UUID | None, Header()] = None,
) -> UUID:
    """Scope all temporary development requests to one explicit user UUID."""
    return x_development_user_id or DEFAULT_DEVELOPMENT_USER_ID


def get_transaction_service(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[UUID, Depends(get_development_user_id)],
) -> TransactionService:
    return TransactionService(TransactionRepository(session), user_id)
