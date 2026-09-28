from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest
from cryptography.fernet import Fernet

from app.core.config import Settings
from app.services.gmail_oauth import (
    GmailOAuthConfigurationError,
    GmailOAuthStateError,
    build_authorization_request,
    verify_state,
)


def _settings() -> Settings:
    return Settings(
        gmail_client_id="client-id",
        gmail_client_secret="client-secret",
        gmail_redirect_uri="http://localhost:8000/auth/gmail/callback",
        gmail_oauth_state_secret="state-secret",
        gmail_token_encryption_key=Fernet.generate_key().decode(),
    )


def test_authorization_url_uses_readonly_scope_and_signed_state() -> None:
    request = build_authorization_request(
        _settings(),
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        account_id=UUID("00000000-0000-0000-0000-000000000010"),
    )
    query = parse_qs(urlparse(request.authorization_url).query)
    assert query["scope"] == ["https://www.googleapis.com/auth/gmail.readonly"]
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]
    assert query["redirect_uri"] == ["http://localhost:8000/auth/gmail/callback"]
    assert len(query["state"][0].split(".")) == 2
    assert request.expires_in_seconds == 600
    assert verify_state("state-secret", query["state"][0]) == (
        UUID("00000000-0000-0000-0000-000000000001"),
        UUID("00000000-0000-0000-0000-000000000010"),
    )


def test_rejects_altered_oauth_state() -> None:
    request = build_authorization_request(
        _settings(),
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        account_id=UUID("00000000-0000-0000-0000-000000000010"),
    )
    state = parse_qs(urlparse(request.authorization_url).query)["state"][0]
    with pytest.raises(GmailOAuthStateError):
        verify_state("different-secret", state)


def test_authorization_requires_complete_server_side_configuration() -> None:
    with pytest.raises(GmailOAuthConfigurationError):
        build_authorization_request(
            Settings(
                gmail_client_id=None,
                gmail_client_secret=None,
                gmail_redirect_uri=None,
                gmail_oauth_state_secret=None,
            ),
            user_id=UUID("00000000-0000-0000-0000-000000000001"),
            account_id=UUID("00000000-0000-0000-0000-000000000010"),
        )
