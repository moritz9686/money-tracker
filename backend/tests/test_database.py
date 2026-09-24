from unittest.mock import MagicMock, Mock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import OperationalError

from app.db import session
from app.db.session import DatabaseUnavailableError


def test_database_check_executes_non_sensitive_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = Mock()
    connection.execute = Mock()
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection
    monkeypatch.setattr(session, "get_engine", lambda: engine)

    session.check_database_connection()

    connection.execute.assert_called_once()


def test_database_check_hides_driver_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = Mock()
    engine.connect.side_effect = OperationalError("SELECT 1", {}, Exception("refused"))
    monkeypatch.setattr(session, "get_engine", lambda: engine)

    with pytest.raises(
        DatabaseUnavailableError, match="Database connection is unavailable"
    ):
        session.check_database_connection()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_database_health_returns_service_unavailable_when_connection_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.main import app

    monkeypatch.setattr(
        "app.main.check_database_connection",
        Mock(side_effect=DatabaseUnavailableError("unavailable")),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/database")

    assert response.status_code == 503
    assert response.json() == {
        "detail": {"code": "HTTP_ERROR", "message": "Database unavailable"}
    }
