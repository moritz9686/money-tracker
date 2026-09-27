from uuid import UUID

from app.services.gmail_ingestion import GmailImportService
from tests.test_deduplication import InMemoryDeduplicationRepository

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
ACCOUNT_ID = UUID("00000000-0000-0000-0000-000000000010")


class GmailRepository(InMemoryDeduplicationRepository):
    def get_account(self, account_id: UUID, user_id: UUID) -> object | None:
        return object() if (account_id, user_id) == (ACCOUNT_ID, USER_ID) else None


def _message(subject: str, snippet: str) -> dict[str, object]:
    return {
        "id": "synthetic-message",
        "internalDate": "1782388800000",
        "snippet": snippet,
        "payload": {"headers": [{"name": "Subject", "value": subject}]},
    }


def test_import_is_idempotent_and_ignores_unknown_email() -> None:
    repository = GmailRepository()
    service = GmailImportService(repository)  # type: ignore[arg-type]
    transaction = _message(
        "HDFC Bank: UPI transaction alert",
        "Rs. 500.25 debited from account ending 1234 to Swiggy. UTR ABCD123456",
    )

    first = service.import_messages(
        user_id=USER_ID,
        account_id=ACCOUNT_ID,
        messages=[transaction, _message("Newsletter", "Welcome to our newsletter")],
    )
    second = service.import_messages(
        user_id=USER_ID, account_id=ACCOUNT_ID, messages=[transaction]
    )

    assert (first.scanned, first.imported, first.unrecognized) == (2, 1, 1)
    assert (second.imported, second.duplicates) == (0, 1)
    assert len(repository.transactions) == 1
    assert repository.transactions[0].description == "UPI SWIGGY HDFC BANK"
    assert "1234" not in repository.transactions[0].description
    assert "ABCD123456" not in repository.transactions[0].description
