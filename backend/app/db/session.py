"""SQLAlchemy engine lifecycle and safe connectivity probing."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


class DatabaseUnavailableError(RuntimeError):
    """Raised when the configured database cannot be safely reached."""


@lru_cache
def get_engine() -> Engine:
    """Create a pooled engine lazily, preventing startup failure without a database."""
    settings = get_settings()
    if not settings.database_url:
        raise DatabaseUnavailableError("Database is not configured")

    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_recycle=settings.database_pool_recycle_seconds,
        connect_args={"connect_timeout": settings.database_connect_timeout_seconds},
    )


def get_session() -> Generator[Session, None, None]:
    """Yield a database session with safe commit, rollback, and close behavior."""
    session_factory = sessionmaker(
        bind=get_engine(), autoflush=False, expire_on_commit=False
    )
    with session_factory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


def check_database_connection() -> None:
    """Confirm database reachability without querying application data."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except (DatabaseUnavailableError, SQLAlchemyError) as error:
        raise DatabaseUnavailableError("Database connection is unavailable") from error


def dispose_engine() -> None:
    """Close pooled connections during process shutdown or test cleanup."""
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    get_engine.cache_clear()
