from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
import pytest

from app.core.auth import SupabaseTokenValidator
from app.core.config import Settings
from app.core.errors import AuthenticationError

USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _token(secret: str, **changes: object) -> str:
    claims = {
        "sub": str(USER_ID),
        "email": "user@example.com",
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        **changes,
    }
    return jwt.encode(claims, secret, algorithm="HS256")


def test_validator_accepts_signed_token_and_uses_subject_as_user_id() -> None:
    secret = "test-secret-that-is-at-least-thirty-two-bytes"
    validator = SupabaseTokenValidator(Settings(supabase_jwt_secret=secret))
    user = validator.validate(_token(secret))
    assert user.id == USER_ID
    assert user.email == "user@example.com"


@pytest.mark.parametrize(
    "token", ["invalid", _token("other-secret-that-is-at-least-thirty-two-bytes")]
)
def test_validator_rejects_invalid_tokens(token: str) -> None:
    validator = SupabaseTokenValidator(
        Settings(supabase_jwt_secret="test-secret-that-is-at-least-thirty-two-bytes")
    )
    with pytest.raises(AuthenticationError):
        validator.validate(token)
