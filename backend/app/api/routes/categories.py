"""Authenticated category reference data."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_transaction_service
from app.db.models import Category
from app.schemas.category import CategoryRead
from app.services.transactions import TransactionService

router = APIRouter(prefix="/categories", tags=["categories"])
ServiceDependency = Annotated[TransactionService, Depends(get_transaction_service)]


@router.get("", response_model=list[CategoryRead])
def list_categories(service: ServiceDependency) -> list[Category]:
    """Return categories owned by the caller, never another user's data."""
    return list(
        service.repository.session.query(Category)
        .filter(Category.user_id == service.user_id)
        .order_by(Category.name, Category.id)
        .all()
    )
