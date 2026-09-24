"""Transaction REST endpoints."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import get_transaction_service
from app.core.errors import InputValidationError
from app.db.models import PaymentMode, TransactionType
from app.schemas.transaction import (
    ErrorResponse,
    TransactionCreate,
    TransactionPage,
    TransactionRead,
    TransactionUpdate,
)
from app.services.transactions import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])
ServiceDependency = Annotated[TransactionService, Depends(get_transaction_service)]
ErrorResponses = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


@router.post(
    "",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    responses=ErrorResponses,
)
def create_transaction(
    payload: TransactionCreate, service: ServiceDependency
) -> TransactionRead:
    return service.create(payload)


@router.get("", response_model=TransactionPage, responses=ErrorResponses)
def list_transactions(
    service: ServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    transaction_type: TransactionType | None = None,
    payment_mode: PaymentMode | None = None,
    category_id: UUID | None = None,
    bank_name: Annotated[str | None, Query(max_length=120)] = None,
    account_id: UUID | None = None,
    merchant: Annotated[str | None, Query(max_length=255)] = None,
    sort: Literal["asc", "desc"] = "desc",
) -> TransactionPage:
    if start_date and end_date and start_date > end_date:
        raise InputValidationError("start_date must not be after end_date")
    items, total = service.list(
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        payment_mode=payment_mode,
        category_id=category_id,
        bank_name=bank_name,
        account_id=account_id,
        merchant=merchant,
        sort_descending=sort == "desc",
        limit=limit,
        offset=offset,
    )
    return TransactionPage(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{transaction_id}", response_model=TransactionRead, responses=ErrorResponses
)
def get_transaction(
    transaction_id: UUID, service: ServiceDependency
) -> TransactionRead:
    return service.get(transaction_id)


@router.patch(
    "/{transaction_id}", response_model=TransactionRead, responses=ErrorResponses
)
def update_transaction(
    transaction_id: UUID, payload: TransactionUpdate, service: ServiceDependency
) -> TransactionRead:
    return service.update(transaction_id, payload)


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ErrorResponses,
)
def delete_transaction(transaction_id: UUID, service: ServiceDependency) -> Response:
    service.delete(transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
