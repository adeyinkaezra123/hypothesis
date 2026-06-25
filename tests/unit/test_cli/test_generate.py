"""End-to-end tests for the ``hypothesis generate`` command."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from typer.testing import CliRunner

from hypothesis.cli.app import app

runner = CliRunner()


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    """A file-backed SQLite DB with a parent/child foreign-key relationship."""
    url = f"sqlite:///{tmp_path / 'gen.db'}"
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE users ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "email VARCHAR(255) NOT NULL)"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE posts ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "user_id INTEGER NOT NULL REFERENCES users(id), "
                "title VARCHAR(200) NOT NULL)"
            )
        )
    engine.dispose()
    return url


def _scalar(url: str, sql: str) -> int:
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            return int(conn.execute(text(sql)).scalar() or 0)
    finally:
        engine.dispose()


def test_generate_populates_all_tables(db_url: str) -> None:
    result = runner.invoke(app, ["generate", db_url, "--rows", "8", "--seed", "1"])
    assert result.exit_code == 0, result.output
    assert _scalar(db_url, "SELECT COUNT(*) FROM users") == 8
    assert _scalar(db_url, "SELECT COUNT(*) FROM posts") == 8


def test_generated_foreign_keys_are_valid(db_url: str) -> None:
    result = runner.invoke(app, ["generate", db_url, "--rows", "10", "--seed", "2"])
    assert result.exit_code == 0, result.output
    orphans = _scalar(
        db_url,
        "SELECT COUNT(*) FROM posts p LEFT JOIN users u ON p.user_id = u.id WHERE u.id IS NULL",
    )
    assert orphans == 0


def test_tables_filter_limits_generation(db_url: str) -> None:
    result = runner.invoke(app, ["generate", db_url, "--tables", "users", "--rows", "5", "--seed", "1"])
    assert result.exit_code == 0, result.output
    assert _scalar(db_url, "SELECT COUNT(*) FROM users") == 5
    assert _scalar(db_url, "SELECT COUNT(*) FROM posts") == 0


def test_seed_makes_generation_reproducible(tmp_path: Path) -> None:
    def first_email(name: str) -> str:
        url = f"sqlite:///{tmp_path / name}"
        engine = create_engine(url)
        with engine.begin() as conn:
            conn.execute(
                text("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, email VARCHAR(255) NOT NULL)")
            )
        engine.dispose()
        assert runner.invoke(app, ["generate", url, "--rows", "3", "--seed", "42"]).exit_code == 0
        engine = create_engine(url)
        try:
            with engine.connect() as conn:
                return str(conn.execute(text("SELECT email FROM users ORDER BY id LIMIT 1")).scalar())
        finally:
            engine.dispose()

    assert first_email("a.db") == first_email("b.db")


def test_invalid_rows_exits_2(db_url: str) -> None:
    result = runner.invoke(app, ["generate", db_url, "--rows", "0"])
    assert result.exit_code == 2


def test_malformed_connection_exits_1() -> None:
    result = runner.invoke(app, ["generate", "://nonsense", "--rows", "5"])
    assert result.exit_code == 1


def test_unique_space_exhaustion_stops_gracefully(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'labels.db'}"
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE labels ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "kind VARCHAR(10) NOT NULL CHECK (kind IN ('a', 'b')))"
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX ux_labels_kind ON labels(kind)"))
    engine.dispose()
    # Only two distinct unique values exist; asking for 10 must not abort.
    result = runner.invoke(app, ["generate", url, "--rows", "10", "--seed", "1"])
    assert result.exit_code == 0, result.output
    assert _scalar(url, "SELECT COUNT(*) FROM labels") <= 2


def test_missing_driver_message_is_actionable_and_leak_free() -> None:
    from hypothesis.cli.commands.generate import _missing_driver_message

    message = _missing_driver_message("postgresql://user:secret@localhost/db")
    assert "psycopg2" in message
    assert "uv sync --extra postgres" in message
    assert "secret" not in message  # the DSN / password is never echoed


def test_missing_postgres_driver_exits_cleanly() -> None:
    # psycopg2 isn't installed in the test env: this must be a clean exit, not a crash.
    result = runner.invoke(
        app, ["generate", "postgresql://user:secret@localhost/db", "--rows", "5"]
    )
    assert result.exit_code == 1
    assert not isinstance(result.exception, ModuleNotFoundError)
