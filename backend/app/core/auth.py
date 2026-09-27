"""Supabase access-token verification without storing passwords."""

from dataclasses import dataclass
from uuid import UUID

import jwt
from jwt import InvalidTokenError, PyJWKClient, PyJWKClientError

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    email: str | None


class SupabaseTokenValidator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._jwks_client = (
            PyJWKClient(self.settings.supabase_jwks_url)
            if self.settings.supabase_jwks_url and not self.settings.supabase_jwt_secret
            else None
        )

    def validate(self, token: str) -> AuthenticatedUser:
        try:
            algorithm = jwt.get_unverified_header(token).get("alg")
            if algorithm == "HS256" and self.settings.supabase_jwt_secret:
                claims = jwt.decode(
                    token,
                    self.settings.supabase_jwt_secret,
                    algorithms=["HS256"],
                    audience=self.settings.supabase_jwt_audience,
                    options={"require": ["exp", "sub"]},
                )
            elif algorithm in {"RS256", "ES256"} and self.settings.supabase_url:
                jwks_client = self._jwks_client or PyJWKClient(
                    self.settings.supabase_jwks_url or ""
                )
                key = jwks_client.get_signing_key_from_jwt(token).key
                claims = jwt.decode(
                    token,
                    key,
                    algorithms=[algorithm],
                    audience=self.settings.supabase_jwt_audience,
                    issuer=f"{self.settings.supabase_url.rstrip('/')}/auth/v1",
                    options={"require": ["exp", "sub"]},
                )
            else:
                raise AuthenticationError("Authentication is not configured")
            return AuthenticatedUser(id=UUID(claims["sub"]), email=claims.get("email"))
        except (InvalidTokenError, PyJWKClientError, KeyError, ValueError) as error:
            raise AuthenticationError("Invalid or expired access token") from error
