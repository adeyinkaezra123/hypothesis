"""Tests for the shared schema inspection workflow."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from hypothesis.core.inspection import inspect_database


def test_inspect_database_reflects_classifies_and_summarizes(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'schema.db'}"
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(
            text("CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(255) NOT NULL)")
        )
        conn.execute(
            text(
                "CREATE TABLE posts ("
                "id INTEGER PRIMARY KEY, "
                "user_id INTEGER NOT NULL REFERENCES users(id), "
                "title VARCHAR(200))"
            )
        )
    engine.dispose()

    result = inspect_database(url)

    assert {table.name for table in result.tables} == {"users", "posts"}
    assert result.summary.table_count == 2
    assert result.summary.column_count == 5
    assert result.summary.foreign_key_count == 1
    assert result.cycles == []
    assert result.insertion_order.index("users") < result.insertion_order.index("posts")
    assert result.classifications["users"]["email"].semantic_type.value == "email"
