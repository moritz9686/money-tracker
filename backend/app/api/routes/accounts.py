"""Authenticated, user-scoped financial-account endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.auth import AuthenticatedUser
from app.db.models import FinancialAccount
from app.db.session import get_session
from app.repositories.transactions import TransactionRepository
from app.schemas.account import AccountCreate, AccountRead

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> FinancialAccount:
    repository = TransactionRepository(session)
    repository.get_or_create_user(user.id, user.email)
    return repository.create_account(
        FinancialAccount(
            user_id=user.id,
            display_name=payload.display_name.strip(),
            bank_name=payload.bank_name,
            account_last4=payload.account_last4,
            card_last4=payload.card_last4,
            currency=payload.currency.upper(),
        )
    )


@router.get("", response_model=list[AccountRead])
def list_accounts(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> list[FinancialAccount]:
    return TransactionRepository(session).list_accounts(user.id)
