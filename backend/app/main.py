"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.transactions import router as transactions_router
from app.core.errors import ApplicationError
from app.db.session import (
    DatabaseUnavailableError,
    check_database_connection,
    dispose_engine,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Release database pool connections cleanly when the API stops."""
    yield
    dispose_engine()


app = FastAPI(
    title="Money Tracker API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)
app.include_router(transactions_router)


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
