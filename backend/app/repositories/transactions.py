"""SQLAlchemy persistence operations for user-scoped transactions."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    Category,
    FinancialAccount,
    GmailConnection,
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

    def create_account(self, account: FinancialAccount) -> FinancialAccount:
        self.session.add(account)
        self.session.flush()
        self.session.refresh(account)
        return account

    def list_accounts(self, user_id: UUID) -> list[FinancialAccount]:
        return list(
            self.session.scalars(
                select(FinancialAccount)
                .where(FinancialAccount.user_id == user_id)
                .order_by(FinancialAccount.display_name, FinancialAccount.id)
            ).all()
        )

    def get_gmail_connection(
        self, user_id: UUID, account_id: UUID
    ) -> GmailConnection | None:
        return self.session.scalar(
            select(GmailConnection).where(
                GmailConnection.user_id == user_id,
                GmailConnection.account_id == account_id,
            )
        )

    def upsert_gmail_connection(
        self, *, user_id: UUID, account_id: UUID, encrypted_refresh_token: str
    ) -> GmailConnection:
        connection = self.get_gmail_connection(user_id, account_id)
        if connection is None:
            connection = GmailConnection(
                user_id=user_id,
                account_id=account_id,
                encrypted_refresh_token=encrypted_refresh_token,
            )
            self.session.add(connection)
        else:
            connection.encrypted_refresh_token = encrypted_refresh_token
            connection.is_active = True
            connection.reauthorization_required = False
        self.session.flush()
        return connection

    def list_due_gmail_connections(
        self, before: datetime, limit: int
    ) -> list[GmailConnection]:
        return list(
            self.session.scalars(
                select(GmailConnection)
                .where(
                    GmailConnection.is_active.is_(True),
                    GmailConnection.reauthorization_required.is_(False),
                    (GmailConnection.last_synced_at.is_(None))
                    | (GmailConnection.last_synced_at < before),
                )
                .order_by(
                    GmailConnection.last_synced_at.nullsfirst(), GmailConnection.id
                )
                .limit(limit)
            ).all()
        )

    def mark_gmail_connection_synced(self, connection: GmailConnection) -> None:
        connection.last_synced_at = datetime.now(timezone.utc)
        self.session.flush()

    def require_gmail_reauthorization(self, connection: GmailConnection) -> None:
        connection.reauthorization_required = True
        self.session.flush()

    def delete_gmail_connection(self, connection: GmailConnection) -> None:
        self.session.delete(connection)
        self.session.flush()

    def get_category(self, category_id: UUID, user_id: UUID) -> Category | None:
        return self.session.scalar(
            select(Category).where(
                Category.id == category_id,
                or_(Category.user_id == user_id, Category.user_id.is_(None)),
            )
        )

    def get_or_create_category(self, user_id: UUID, name: str) -> Category:
        category = self.session.scalar(
            select(Category).where(Category.user_id == user_id, Category.name == name)
        )
        if category is None:
            category = Category(user_id=user_id, name=name)
            self.session.add(category)
            self.session.flush()
        return category

    def backfill_deterministic_categories(self, user_id: UUID) -> None:
        from app.services.categorization import deterministic_category

        transactions = self.session.scalars(
            select(Transaction).where(
                Transaction.user_id == user_id, Transaction.category_id.is_(None)
            )
        ).all()
        for transaction in transactions:
            result = deterministic_category(transaction.merchant)
            if result.source == "rule":
                transaction.category_id = self.get_or_create_category(
                    user_id, result.category
                ).id
        self.session.flush()

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
        statement: Select[tuple[Transaction]] = select(Transaction).options(
            selectinload(Transaction.category)
        ).where(
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
        self, user_id: UUID, source: TransactionSource, source_fingerprint: str
    ) -> Transaction | None:
        return self.session.scalar(
            select(Transaction)
            .join(TransactionSourceRecord)
            .where(
                Transaction.user_id == user_id,
                TransactionSourceRecord.user_id == user_id,
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
