"""User-scoped transaction service."""

from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.db.models import Transaction
from app.repositories.transactions import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:
    def __init__(
        self, repository: TransactionRepository, user_id: UUID, email: str | None = None
    ) -> None:
        self.repository = repository
        self.user_id = user_id
        self.email = email

    def create(self, payload: TransactionCreate) -> Transaction:
        self.repository.get_or_create_user(self.user_id, self.email)
        self._validate_account(payload.account_id)
        self._validate_category(payload.category_id)
        transaction = Transaction(user_id=self.user_id, **payload.model_dump())
        try:
            return self.repository.create(transaction)
        except IntegrityError as error:
            self.repository.session.rollback()
            raise ConflictError() from error

    def get(self, transaction_id: UUID) -> Transaction:
        transaction = self.repository.get(transaction_id, self.user_id)
        if transaction is None:
            raise NotFoundError()
        return transaction

    def list(self, **filters: object) -> tuple[list[Transaction], int]:
        return self.repository.list(self.user_id, **filters)  # type: ignore[arg-type]

    def update(self, transaction_id: UUID, payload: TransactionUpdate) -> Transaction:
        transaction = self.get(transaction_id)
        changes = payload.model_dump(exclude_unset=True)
        if "account_id" in changes and changes["account_id"] is not None:
            self._validate_account(changes["account_id"])
        if "category_id" in changes and changes["category_id"] is not None:
            self._validate_category(changes["category_id"])
        for field, value in changes.items():
            setattr(transaction, field, value)
        try:
            return self.repository.create(transaction)
        except IntegrityError as error:
            self.repository.session.rollback()
            raise ConflictError() from error

    def delete(self, transaction_id: UUID) -> None:
        self.repository.delete(self.get(transaction_id))

    def _validate_account(self, account_id: UUID) -> None:
        if self.repository.get_account(account_id, self.user_id) is None:
            raise NotFoundError()

    def _validate_category(self, category_id: UUID | None) -> None:
        if (
            category_id
            and self.repository.get_category(category_id, self.user_id) is None
        ):
            raise NotFoundError()
