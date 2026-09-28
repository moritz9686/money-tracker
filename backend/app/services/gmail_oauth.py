"""Server-side Gmail OAuth request construction without exposing secrets."""

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from urllib.parse import urlencode
from uuid import UUID

from app.core.config import Settings

_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
_STATE_TTL_SECONDS = 600


class GmailOAuthConfigurationError(ValueError):
    """Raised without including secret configuration values."""


class GmailOAuthStateError(ValueError):
    """Raised when an OAuth callback state is invalid, altered, or expired."""


@dataclass(frozen=True)
class GmailAuthorizationRequest:
    authorization_url: str
    expires_in_seconds: int


def build_authorization_request(
    settings: Settings, *, user_id: UUID, account_id: UUID
) -> GmailAuthorizationRequest:
    """Build a short-lived Google consent URL for one owned financial account."""
    if not settings.gmail_oauth_configured:
        raise GmailOAuthConfigurationError("Gmail OAuth is not configured")
    state = _signed_state(settings.gmail_oauth_state_secret or "", user_id, account_id)
    query = urlencode(
        {
            "client_id": settings.gmail_client_id,
            "redirect_uri": settings.gmail_redirect_uri,
            "response_type": "code",
            "scope": _GMAIL_READONLY_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
        }
    )
    return GmailAuthorizationRequest(
        authorization_url=f"{_AUTHORIZE_URL}?{query}",
        expires_in_seconds=_STATE_TTL_SECONDS,
    )


def _signed_state(secret: str, user_id: UUID, account_id: UUID) -> str:
    payload = json.dumps(
        {
            "u": str(user_id),
            "a": str(account_id),
            "e": int(time.time()) + _STATE_TTL_SECONDS,
            "n": secrets.token_urlsafe(16),
        },
        separators=(",", ":"),
    ).encode()
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    return _encode(payload) + "." + _encode(signature)


def verify_state(secret: str, state: str) -> tuple[UUID, UUID]:
    """Verify a callback state without returning its nonce or sensitive content."""
    try:
        encoded_payload, encoded_signature = state.split(".", maxsplit=1)
        payload = _decode(encoded_payload)
        supplied_signature = _decode(encoded_signature)
        expected_signature = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise GmailOAuthStateError("Invalid OAuth state")
        claims = json.loads(payload)
        if not isinstance(claims["e"], int) or claims["e"] < time.time():
            raise GmailOAuthStateError("Expired OAuth state")
        return UUID(claims["u"]), UUID(claims["a"])
    except (
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as error:
        if isinstance(error, GmailOAuthStateError):
            raise
        raise GmailOAuthStateError("Invalid OAuth state") from error


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
