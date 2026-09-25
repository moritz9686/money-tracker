"""SQLAlchemy persistence operations for user-scoped transactions."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.db.models import (
    Category,
    FinancialAccount,
    Transaction,
    TransactionSource,
    TransactionSourceRecord,
    User,
)


class TransactionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_user(self, user_id: UUID, email: str | None) -> User:
        user = self.session.get(User, user_id)
        if user is None:
            user = User(id=user_id, email=email or f"user-{user_id}@local.invalid")
            self.session.add(user)
            self.session.flush()
        return user

    def get_account(self, account_id: UUID, user_id: UUID) -> FinancialAccount | None:
        return self.session.scalar(
            select(FinancialAccount).where(
                FinancialAccount.id == account_id, FinancialAccount.user_id == user_id
            )
        )

    def get_category(self, category_id: UUID, user_id: UUID) -> Category | None:
        return self.session.scalar(
            select(Category).where(
                Category.id == category_id,
                or_(Category.user_id == user_id, Category.user_id.is_(None)),
            )
        )

    def create(self, transaction: Transaction) -> Transaction:
        self.session.add(transaction)
        self.session.flush()
        self.session.refresh(transaction)
        return transaction

    def get(self, transaction_id: UUID, user_id: UUID) -> Transaction | None:
        return self.session.scalar(
            select(Transaction).where(
                Transaction.id == transaction_id, Transaction.user_id == user_id
            )
        )

    def list(
        self,
        user_id: UUID,
        *,
        start_date: datetime | None,
        end_date: datetime | None,
        transaction_type: str | None,
        payment_mode: str | None,
        category_id: UUID | None,
        bank_name: str | None,
        account_id: UUID | None,
        merchant: str | None,
        sort_descending: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[Transaction], int]:
        statement: Select[tuple[Transaction]] = select(Transaction).where(
            Transaction.user_id == user_id
        )
        if start_date:
            statement = statement.where(Transaction.transaction_date >= start_date)
        if end_date:
            statement = statement.where(Transaction.transaction_date <= end_date)
        if transaction_type:
            statement = statement.where(
                Transaction.transaction_type == transaction_type
            )
        if payment_mode:
            statement = statement.where(Transaction.payment_mode == payment_mode)
        if category_id:
            statement = statement.where(Transaction.category_id == category_id)
        if bank_name:
            statement = statement.where(Transaction.bank_name.ilike(f"%{bank_name}%"))
        if account_id:
            statement = statement.where(Transaction.account_id == account_id)
        if merchant:
            statement = statement.where(Transaction.merchant.ilike(f"%{merchant}%"))

        count = self.session.scalar(
            select(func.count()).select_from(statement.subquery())
        )
        date_order = (
            Transaction.transaction_date.desc()
            if sort_descending
            else Transaction.transaction_date.asc()
        )
        rows = self.session.scalars(
            statement.order_by(date_order, Transaction.id).offset(offset).limit(limit)
        ).all()
        return rows, count or 0

    def delete(self, transaction: Transaction) -> None:
        self.session.delete(transaction)
        self.session.flush()

    def find_by_source_fingerprint(
        self, source: TransactionSource, source_fingerprint: str
    ) -> Transaction | None:
        return self.session.scalar(
            select(Transaction)
            .join(TransactionSourceRecord)
            .where(
                TransactionSourceRecord.source == source,
                TransactionSourceRecord.source_fingerprint == source_fingerprint,
            )
        )

    def find_by_reference(self, user_id: UUID, reference_id: str) -> Transaction | None:
        return self.session.scalar(
            select(Transaction)
            .outerjoin(TransactionSourceRecord)
            .where(
                Transaction.user_id == user_id,
                or_(
                    Transaction.reference_id == reference_id,
                    TransactionSourceRecord.reference_id == reference_id,
                ),
            )
        )

    def find_by_fingerprint(
        self, user_id: UUID, fingerprint: str
    ) -> Transaction | None:
        return self.session.scalar(
            select(Transaction).where(
                Transaction.user_id == user_id, Transaction.fingerprint == fingerprint
            )
        )

    def create_transaction(self, transaction: Transaction) -> Transaction:
        return self.create(transaction)

    def record_source(self, source_record: TransactionSourceRecord) -> None:
        self.session.add(source_record)
        self.session.flush()
