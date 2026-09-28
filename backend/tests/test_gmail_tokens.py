import pytest
from cryptography.fernet import Fernet

from app.core.config import Settings
from app.services.gmail_tokens import GmailTokenCipher, GmailTokenError


def test_refresh_tokens_are_encrypted_and_round_trip() -> None:
    cipher = GmailTokenCipher(
        Settings(gmail_token_encryption_key=Fernet.generate_key().decode())
    )
    encrypted = cipher.encrypt("synthetic-refresh-token")

    assert encrypted != "synthetic-refresh-token"
    assert cipher.decrypt(encrypted) == "synthetic-refresh-token"


def test_missing_encryption_key_is_rejected() -> None:
    with pytest.raises(GmailTokenError):
        GmailTokenCipher(Settings())
