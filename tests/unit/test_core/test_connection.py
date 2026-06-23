"""Tests for database connection helpers."""

from __future__ import annotations

from typing import Literal

import pytest
from sqlalchemy import create_engine, text

from hypothesis.core.connection import (
    DatabaseConnection,
    _max_pk_statement,
    _split_table_identifier,
)


def test_split_table_identifier_supports_optional_schema() -> None:
    assert _split_table_identifier("users") == (None, "users")
    assert _split_table_identifier("public.users") == ("public", "users")


@pytest.mark.parametrize("identifier", ["", ".users", "public.", "a.b.c", "bad\x00name"])
def test_split_table_identifier_rejects_invalid_names(identifier: str) -> None:
    with pytest.raises(ValueError):
        _split_table_identifier(identifier)


def test_max_pk_statement_quotes_identifiers() -> None:
    statement = _max_pk_statement("public.user accounts", "id value")
    compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))

    assert '"public"."user accounts"' in compiled
    assert '"id value"' in compiled


def test_max_pk_statement_rejects_invalid_column() -> None:
    with pytest.raises(ValueError):
        _max_pk_statement("users", "")


def test_get_next_sequence_value_uses_quoted_identifiers(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE "odd table" ("id value" INTEGER PRIMARY KEY)'))
        conn.execute(text('INSERT INTO "odd table" ("id value") VALUES (41)'))

    db = object.__new__(DatabaseConnection)
    db.connection_string = "sqlite://"
    db.engine = engine

    def fake_dialect() -> Literal["postgresql"]:
        return "postgresql"

    monkeypatch.setattr(db, "get_dialect", fake_dialect)

    try:
        assert db.get_next_sequence_value("odd table", "id value") == 42
    finally:
        engine.dispose()


def test_validate_returns_true_for_usable_connection() -> None:
    db = object.__new__(DatabaseConnection)
    db.connection_string = "sqlite://"
    db.engine = create_engine("sqlite://")
    db.engine.dispose()

    assert db.validate() is True
    db.close()
