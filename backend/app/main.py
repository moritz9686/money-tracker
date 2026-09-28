"""FastAPI application entry point."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.api.routes.accounts import router as accounts_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.gmail import router as gmail_router
from app.api.routes.transactions import router as transactions_router
from app.core.config import get_settings
from app.core.errors import ApplicationError
from app.core.rate_limit import RateLimitMiddleware
from app.db.session import (
    DatabaseUnavailableError,
    check_database_connection,
    dispose_engine,
    get_engine,
)
from app.repositories.transactions import TransactionRepository
from app.services.gmail_sync import GmailSyncService


@asynccontextmanager
async def _gmail_background_loop() -> None:
    while True:
        await asyncio.sleep(settings.gmail_sync_interval_seconds)
        try:
            await asyncio.to_thread(_run_due_gmail_sync)
        except Exception:
            logging.getLogger(__name__).warning("gmail background sync failed")


def _run_due_gmail_sync() -> None:
    from sqlalchemy.orm import Session

    with Session(get_engine()) as session:
        GmailSyncService(
            TransactionRepository(session), settings
        ).sync_due_connections()
        session.commit()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Release database pool connections cleanly when the API stops."""
    task = None
    if settings.gmail_background_sync_enabled and settings.gmail_oauth_configured:
        task = asyncio.create_task(_gmail_background_loop())
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        dispose_engine()


settings = get_settings()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
app = FastAPI(
    title="Money Tracker API",
    version="0.1.0",
    docs_url="/docs" if settings.api_docs_enabled else None,
    redoc_url=None,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)
app.add_middleware(
    RateLimitMiddleware,
    requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)
app.include_router(transactions_router)
app.include_router(accounts_router)
app.include_router(analytics_router)
app.include_router(gmail_router)


@app.exception_handler(ApplicationError)
async def application_error_handler(
    _: Request, error: ApplicationError
) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": {"code": error.code, "message": error.message}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _: Request, error: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": {"code": "VALIDATION_ERROR", "message": "Invalid request"}},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, error: HTTPException) -> JSONResponse:
    message = error.detail if isinstance(error.detail, str) else "Request failed"
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": {"code": "HTTP_ERROR", "message": message}},
    )


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Return a lightweight health signal without exposing sensitive details."""
    return {"status": "ok"}


@app.get("/health/database", tags=["system"])
def database_health_check() -> dict[str, str]:
    """Report whether the configured PostgreSQL service is reachable."""
    try:
        check_database_connection()
    except DatabaseUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from error
    return {"status": "ok"}
