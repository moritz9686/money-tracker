"""Environment-based application settings."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded exclusively from environment variables or an ignored .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str | None = None
    database_pool_size: int = Field(default=5, ge=1, le=20)
    database_max_overflow: int = Field(default=5, ge=0, le=20)
    database_pool_recycle_seconds: int = Field(default=1800, ge=60)
    database_connect_timeout_seconds: int = Field(default=10, ge=1, le=60)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str | None) -> str | None:
        """Require the explicitly selected psycopg PostgreSQL driver."""
        if value is not None and not value.startswith("postgresql+psycopg://"):
            msg = "DATABASE_URL must start with postgresql+psycopg://"
            raise ValueError(msg)
        return value


@lru_cache
def get_settings() -> Settings:
    """Return one immutable settings instance per running process."""
    return Settings()
