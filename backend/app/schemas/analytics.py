"""Exact-money analytics response contracts."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class AnalyticsBreakdown(BaseModel):
    label: str
    amount: Decimal


class MonthlyAnalytics(BaseModel):
    month: date
    income: Decimal
    expenses: Decimal
    net_cash_flow: Decimal
    category_spending: list[AnalyticsBreakdown]
    payment_mode_spending: list[AnalyticsBreakdown]
    bank_account_spending: list[AnalyticsBreakdown]
    daily_spending: list[AnalyticsBreakdown]
    previous_month_expenses: Decimal
    expense_change: Decimal
    top_merchants: list[AnalyticsBreakdown]
    largest_transactions: list[AnalyticsBreakdown]
