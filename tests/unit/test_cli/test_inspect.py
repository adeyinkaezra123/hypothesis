"""Tests for the ``hypothesis inspect`` command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from typer.testing import CliRunner

from hypothesis.cli.app import app

runner = CliRunner()


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    """A file-backed SQLite database the CLI can open by URL."""
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
    return url


def test_table_format_lists_tables_and_insertion_order(db_url: str) -> None:
    result = runner.invoke(app, ["inspect", db_url])
    assert result.exit_code == 0, result.output
    assert "users" in result.output
    assert "posts" in result.output
    assert "Insertion order" in result.output


def test_json_format_is_machine_readable(db_url: str) -> None:
    result = runner.invoke(app, ["inspect", db_url, "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert {table["name"] for table in data} == {"users", "posts"}


def test_markdown_format(db_url: str) -> None:
    result = runner.invoke(app, ["inspect", db_url, "-f", "markdown"])
    assert result.exit_code == 0, result.output
    assert "## users" in result.output
    assert "## posts" in result.output


def test_tables_filter_limits_output(db_url: str) -> None:
    result = runner.invoke(app, ["inspect", db_url, "--tables", "users"])
    assert result.exit_code == 0, result.output
    assert "users" in result.output
    assert "posts" not in result.output


def test_verbose_shows_foreign_key_relationships(db_url: str) -> None:
    result = runner.invoke(app, ["inspect", db_url, "--verbose"])
    assert result.exit_code == 0, result.output
    assert "users.id" in result.output


def test_invalid_format_exits_2(db_url: str) -> None:
    result = runner.invoke(app, ["inspect", db_url, "-f", "yaml"])
    assert result.exit_code == 2


def test_malformed_connection_exits_1() -> None:
    result = runner.invoke(app, ["inspect", "://nonsense"])
    assert result.exit_code == 1


def test_table_output_includes_semantic_column(db_url: str) -> None:
    result = runner.invoke(app, ["inspect", db_url])
    assert result.exit_code == 0, result.output
    assert "Semantic" in result.output


def test_json_includes_semantic_classification(db_url: str) -> None:
    result = runner.invoke(app, ["inspect", db_url, "-f", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    users = next(table for table in data if table["name"] == "users")
    email = next(col for col in users["columns"] if col["name"] == "email")
    assert email["semantic_type"] == "email"
    assert "confidence" in email
    assert email["needs_review"] is False
