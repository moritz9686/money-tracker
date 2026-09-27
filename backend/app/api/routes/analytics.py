from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_transaction_service
from app.schemas.analytics import MonthlyAnalytics
from app.services.analytics import AnalyticsService
from app.services.transactions import TransactionService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/monthly", response_model=MonthlyAnalytics)
def monthly_analytics(
    service: Annotated[TransactionService, Depends(get_transaction_service)],
    month: Annotated[date, Query(description="Any date in the requested month")],
) -> MonthlyAnalytics:
    return AnalyticsService(service).monthly(month)
