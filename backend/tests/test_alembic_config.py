from pathlib import Path


def test_alembic_escapes_url_encoded_database_passwords() -> None:
    environment = Path("backend/alembic/env.py").read_text()

    assert 'settings.database_url.replace("%", "%%")' in environment
