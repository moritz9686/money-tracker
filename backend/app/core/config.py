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
    supabase_url: str | None = None
    supabase_jwt_secret: str | None = None
    supabase_jwt_audience: str = "authenticated"
    gmail_client_id: str | None = None
    gmail_client_secret: str | None = None
    gmail_redirect_uri: str | None = None
    gmail_oauth_state_secret: str | None = None
    ai_provider: str | None = None
    ai_api_key: str | None = None
    cors_allowed_origins: str = ""
    rate_limit_requests: int = Field(default=120, ge=1, le=10000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    api_docs_enabled: bool = True

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str | None) -> str | None:
        """Require the explicitly selected psycopg PostgreSQL driver."""
        if value is not None and not value.startswith("postgresql+psycopg://"):
            msg = "DATABASE_URL must start with postgresql+psycopg://"
            raise ValueError(msg)
        return value

    @field_validator("supabase_jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str | None) -> str | None:
        if value is not None and len(value) < 32:
            raise ValueError("SUPABASE_JWT_SECRET must be at least 32 characters")
        return value

    @property
    def gmail_oauth_configured(self) -> bool:
        """Return whether all server-side Gmail OAuth settings are present."""
        return all(
            (
                self.gmail_client_id,
                self.gmail_client_secret,
                self.gmail_redirect_uri,
                self.gmail_oauth_state_secret,
            )
        )

    @property
    def supabase_jwks_url(self) -> str | None:
        if self.supabase_url is None:
            return None
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"

    @property
    def cors_origins(self) -> list[str]:
        origins = [
            item.strip()
            for item in self.cors_allowed_origins.split(",")
            if item.strip()
        ]
        if self.app_env == "production" and "*" in origins:
            raise ValueError("CORS_ALLOWED_ORIGINS cannot contain * in production")
        return origins


@lru_cache
def get_settings() -> Settings:
    """Return one immutable settings instance per running process."""
    return Settings()
