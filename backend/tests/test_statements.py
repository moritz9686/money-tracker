from decimal import Decimal

import pytest

from app.db.models import TransactionType
from app.services.statements import (
    MAXIMUM_STATEMENT_BYTES,
    UnsupportedStatementError,
    parse_statement,
)


def test_parses_synthetic_hdfc_csv() -> None:
    content = (
        b"HDFC Bank,Date,Description,Debit,Credit,Reference,Account Number\n"
        b",24/09/2026,UPI/Swiggy/ABC,500.25,,UTR123456,XXXX1234\n"
    )
    parser, rows = parse_statement(content, "synthetic.csv")
    assert parser.bank_name == "HDFC"
    assert rows[0].amount == Decimal("500.25")
    assert rows[0].transaction_type == TransactionType.DEBIT
    assert rows[0].account_last4 == "1234"


def test_rejects_unknown_format_without_exposing_content() -> None:
    with pytest.raises(UnsupportedStatementError):
        parse_statement(b"secret", "statement.doc")


@pytest.mark.parametrize("filename", ["malformed.pdf", "malformed.xlsx"])
def test_rejects_malformed_supported_files_safely(filename: str) -> None:
    with pytest.raises(UnsupportedStatementError, match="Malformed or unreadable"):
        parse_statement(b"not a statement", filename)


def test_rejects_oversized_statement_before_parsing() -> None:
    with pytest.raises(UnsupportedStatementError, match="15 MB"):
        parse_statement(b"x" * (MAXIMUM_STATEMENT_BYTES + 1), "large.csv")
