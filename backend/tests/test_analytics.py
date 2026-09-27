from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.db.models import PaymentMode, TransactionType
from app.services.analytics import AnalyticsService


class FakeTransactions:
    def list(self, **_: object):
        return [
            SimpleNamespace(
                amount=Decimal("85000.00"),
                transaction_type=TransactionType.CREDIT,
                payment_mode=PaymentMode.OTHER,
                category_id=None,
                bank_name="HDFC",
                account_last4="1234",
                transaction_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
                merchant="Salary",
                description=None,
            ),
            SimpleNamespace(
                amount=Decimal("42350.00"),
                transaction_type=TransactionType.DEBIT,
                payment_mode=PaymentMode.UPI,
                category_id=None,
                bank_name="HDFC",
                account_last4="1234",
                transaction_date=datetime(2026, 9, 2, tzinfo=timezone.utc),
                merchant="Swiggy",
                description=None,
            ),
        ], 2


def test_monthly_analytics_uses_exact_decimal_money() -> None:
    result = AnalyticsService(FakeTransactions()).monthly(date(2026, 9, 15))
    assert result.income == Decimal("85000.00")
    assert result.expenses == Decimal("42350.00")
    assert result.net_cash_flow == Decimal("42650.00")
    assert result.top_merchants[0].label == "Swiggy"
