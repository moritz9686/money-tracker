from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import DEFAULT_DEVELOPMENT_USER_ID, get_transaction_service
from app.core.errors import ConflictError, NotFoundError
from app.db.models import PaymentMode, TransactionSource, TransactionType
from app.main import app

USER_ID = DEFAULT_DEVELOPMENT_USER_ID
ACCOUNT_ID = UUID("00000000-0000-0000-0000-000000000010")
CATEGORY_ID = UUID("00000000-0000-0000-0000-000000000020")
TRANSACTION_ID = UUID("00000000-0000-0000-0000-000000000030")


def make_transaction() -> SimpleNamespace:
    timestamp = datetime(2026, 9, 24, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=TRANSACTION_ID,
        user_id=USER_ID,
        account_id=ACCOUNT_ID,
        transaction_date=timestamp,
        amount=Decimal("500.25"),
        currency="INR",
        transaction_type=TransactionType.DEBIT,
        payment_mode=PaymentMode.UPI,
        merchant="Swiggy",
        description="Dinner",
        bank_name="Example Bank",
        account_last4="1234",
        card_last4=None,
        upi_id="user@example",
        reference_id="REF-123",
        category_id=CATEGORY_ID,
        source=TransactionSource.MANUAL,
        confidence=Decimal("1.000"),
        fingerprint="a" * 64,
        created_at=timestamp,
        updated_at=timestamp,
    )


class FakeTransactionService:
    def __init__(self) -> None:
        self.transaction = make_transaction()
        self.list_filters: dict[str, object] | None = None
        self.deleted_id: UUID | None = None

    def create(self, payload: object) -> SimpleNamespace:
        return self.transaction

    def list(self, **filters: object) -> tuple[list[SimpleNamespace], int]:
        self.list_filters = filters
        return [self.transaction], 1

    def get(self, transaction_id: UUID) -> SimpleNamespace:
        if transaction_id != TRANSACTION_ID:
            raise NotFoundError()
        return self.transaction

    def update(self, transaction_id: UUID, payload: object) -> SimpleNamespace:
        return self.get(transaction_id)

    def delete(self, transaction_id: UUID) -> None:
        self.get(transaction_id)
        self.deleted_id = transaction_id


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def transaction_service() -> FakeTransactionService:
    service = FakeTransactionService()
    app.dependency_overrides[get_transaction_service] = lambda: service
    yield service
    app.dependency_overrides.clear()


@pytest.fixture
async def client(transaction_service: FakeTransactionService) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as api_client:
        yield api_client


def transaction_payload() -> dict[str, object]:
    return {
        "account_id": str(ACCOUNT_ID),
        "transaction_date": "2026-09-24T12:00:00Z",
        "amount": "500.25",
        "currency": "inr",
        "transaction_type": "DEBIT",
        "payment_mode": "UPI",
        "merchant": "Swiggy",
        "source": "MANUAL",
        "fingerprint": "a" * 64,
    }


@pytest.mark.anyio
async def test_create_transaction_returns_created_transaction(
    client: AsyncClient,
) -> None:
    response = await client.post("/transactions", json=transaction_payload())

    assert response.status_code == 201
    assert response.json()["id"] == str(TRANSACTION_ID)
    assert response.json()["amount"] == "500.25"


@pytest.mark.anyio
async def test_list_transactions_passes_filters_and_pagination(
    client: AsyncClient, transaction_service: FakeTransactionService
) -> None:
    response = await client.get(
        "/transactions",
        params={
            "limit": 10,
            "offset": 5,
            "start_date": "2026-09-01T00:00:00Z",
            "end_date": "2026-09-30T00:00:00Z",
            "transaction_type": "DEBIT",
            "payment_mode": "UPI",
            "category_id": str(CATEGORY_ID),
            "bank_name": "Example",
            "account_id": str(ACCOUNT_ID),
            "merchant": "swig",
            "sort": "asc",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["limit"] == 10
    assert transaction_service.list_filters == {
        "start_date": datetime(2026, 9, 1, tzinfo=timezone.utc),
        "end_date": datetime(2026, 9, 30, tzinfo=timezone.utc),
        "transaction_type": TransactionType.DEBIT,
        "payment_mode": PaymentMode.UPI,
        "category_id": CATEGORY_ID,
        "bank_name": "Example",
        "account_id": ACCOUNT_ID,
        "merchant": "swig",
        "sort_descending": False,
        "limit": 10,
        "offset": 5,
    }


@pytest.mark.anyio
async def test_get_update_and_delete_transaction(
    client: AsyncClient, transaction_service: FakeTransactionService
) -> None:
    get_response = await client.get(f"/transactions/{TRANSACTION_ID}")
    update_response = await client.patch(
        f"/transactions/{TRANSACTION_ID}", json={"merchant": "Swiggy Instamart"}
    )
    delete_response = await client.delete(f"/transactions/{TRANSACTION_ID}")

    assert get_response.status_code == 200
    assert update_response.status_code == 200
    assert delete_response.status_code == 204
    assert transaction_service.deleted_id == TRANSACTION_ID


@pytest.mark.anyio
async def test_validation_and_not_found_errors_have_consistent_shape(
    client: AsyncClient,
) -> None:
    invalid_amount = await client.post(
        "/transactions", json={**transaction_payload(), "amount": "0"}
    )
    invalid_dates = await client.get(
        "/transactions",
        params={
            "start_date": "2026-10-01T00:00:00Z",
            "end_date": "2026-09-01T00:00:00Z",
        },
    )
    missing = await client.get("/transactions/00000000-0000-0000-0000-000000000099")
    invalid_patch = await client.patch(
        f"/transactions/{TRANSACTION_ID}", json={"amount": None}
    )

    assert invalid_amount.status_code == 422
    assert invalid_amount.json()["detail"]["code"] == "VALIDATION_ERROR"
    assert invalid_dates.status_code == 422
    assert invalid_dates.json()["detail"] == {
        "code": "VALIDATION_ERROR",
        "message": "start_date must not be after end_date",
    }
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "NOT_FOUND"
    assert invalid_patch.status_code == 422
    assert invalid_patch.json()["detail"]["code"] == "VALIDATION_ERROR"


@pytest.mark.anyio
async def test_conflict_error_is_returned_as_409(client: AsyncClient) -> None:
    app.dependency_overrides[get_transaction_service] = lambda: SimpleNamespace(
        create=lambda _: (_ for _ in ()).throw(ConflictError())
    )

    response = await client.post("/transactions", json=transaction_payload())

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "CONFLICT"
