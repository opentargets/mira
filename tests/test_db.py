import pytest

from mira.utils.db import _build_select_query, construct_db_uri


def test_construct_db_uri_quotes_credentials() -> None:
    assert (
        construct_db_uri(
            "postgresql",
            "localhost:5432/db",
            db_user="user@example",
            db_password="p@ss:/word",
        )
        == "postgresql://user%40example:p%40ss%3A%2Fword@localhost:5432/db"
    )


@pytest.mark.parametrize(
    ("db_user", "db_password"),
    [("user", None), (None, "password"), ("", "password"), ("user", "")],
)
def test_construct_db_uri_rejects_partial_credentials(
    db_user: str | None, db_password: str | None
) -> None:
    with pytest.raises(ValueError, match="set together"):
        construct_db_uri("postgresql", "localhost/db", db_user, db_password)


def test_build_select_query_coerces_limit() -> None:
    assert _build_select_query("table", "schema", limit="5") == (
        "SELECT DISTINCT * FROM schema.table LIMIT 5"
    )


def test_build_select_query_documents_raw_where_clause() -> None:
    assert _build_select_query("table", "schema", where_clause="id > 1") == (
        "SELECT DISTINCT * FROM schema.table WHERE id > 1"
    )
