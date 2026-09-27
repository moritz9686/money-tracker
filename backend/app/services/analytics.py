"""Deterministic user-scoped analytics using Decimal only."""

from collections import defaultdict
from datetime import date, datetime, time, timezone
from decimal import Decimal

from app.db.models import Transaction, TransactionType
from app.schemas.analytics import AnalyticsBreakdown, MonthlyAnalytics


class AnalyticsService:
    def __init__(self, transaction_service: object) -> None:
        self.transaction_service = transaction_service

    def monthly(self, month: date) -> MonthlyAnalytics:
        start = datetime.combine(month.replace(day=1), time.min, tzinfo=timezone.utc)
        next_month = date(month.year + (month.month == 12), month.month % 12 + 1, 1)
        end = datetime.combine(next_month, time.min, tzinfo=timezone.utc)
        items, _ = self.transaction_service.list(
            start_date=start,
            end_date=end,
            transaction_type=None,
            payment_mode=None,
            category_id=None,
            bank_name=None,
            account_id=None,
            merchant=None,
            sort_descending=True,
            limit=10000,
            offset=0,
        )
        transactions: list[Transaction] = list(items)
        income = sum(
            (
                item.amount
                for item in transactions
                if item.transaction_type == TransactionType.CREDIT
            ),
            Decimal(),
        )
        expenses = sum(
            (
                item.amount
                for item in transactions
                if item.transaction_type == TransactionType.DEBIT
            ),
            Decimal(),
        )

        def breakdown(key: object) -> list[AnalyticsBreakdown]:
            totals: dict[str, Decimal] = defaultdict(Decimal)
            for item in transactions:
                if item.transaction_type == TransactionType.DEBIT:
                    totals[str(key(item))] += item.amount
            return [
                AnalyticsBreakdown(label=k, amount=v)
                for k, v in sorted(totals.items(), key=lambda row: row[1], reverse=True)
            ]

        categories = breakdown(lambda item: str(item.category_id or "Uncategorized"))
        modes = breakdown(lambda item: item.payment_mode.value)
        banks = breakdown(
            lambda item: item.bank_name or item.account_last4 or "Unknown account"
        )
        daily = breakdown(lambda item: item.transaction_date.date().isoformat())
        merchants = breakdown(lambda item: item.merchant or "Unknown merchant")[:10]
        largest = [
            AnalyticsBreakdown(
                label=item.merchant or item.description or "Unknown", amount=item.amount
            )
            for item in sorted(
                transactions, key=lambda item: item.amount, reverse=True
            )[:10]
        ]
        return MonthlyAnalytics(
            month=month.replace(day=1),
            income=income,
            expenses=expenses,
            net_cash_flow=income - expenses,
            category_spending=categories,
            payment_mode_spending=modes,
            bank_account_spending=banks,
            daily_spending=daily,
            previous_month_expenses=Decimal(),
            expense_change=Decimal(),
            top_merchants=merchants,
            largest_transactions=largest,
        )
