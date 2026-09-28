"""Encryption of Google refresh tokens; plaintext must never reach persistence."""

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import Settings


class GmailTokenError(RuntimeError):
    """Safe token-storage failure without credential details."""


class GmailTokenCipher:
    def __init__(self, settings: Settings) -> None:
        if not settings.gmail_token_encryption_key:
            raise GmailTokenError("Gmail token encryption is not configured")
        try:
            self._fernet = Fernet(settings.gmail_token_encryption_key.encode())
        except (TypeError, ValueError) as error:
            raise GmailTokenError("Gmail token encryption is not configured") from error

    def encrypt(self, refresh_token: str) -> str:
        return self._fernet.encrypt(refresh_token.encode()).decode()

    def decrypt(self, encrypted_refresh_token: str) -> str:
        try:
            return self._fernet.decrypt(encrypted_refresh_token.encode()).decode()
        except (InvalidToken, UnicodeDecodeError) as error:
            raise GmailTokenError("Stored Gmail connection cannot be used") from error
