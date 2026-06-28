"""MySQL integration tests for the generate CLI.

These tests require a real MySQL URL and are skipped by default:

- HYPOTHESIS_TEST_MYSQL_URL=mysql+pymysql://...

InnoDB is requested explicitly so the foreign key is enforced (MyISAM parses
but ignores FK clauses), which is what makes the orphan check meaningful.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from typer.testing import CliRunner

from hypothesis.cli.app import app

runner = CliRunner()


@pytest.fixture
def mysql_url() -> Iterator[str]:
    url = os.getenv("HYPOTHESIS_TEST_MYSQL_URL")
    if not url:
        pytest.skip("HYPOTHESIS_TEST_MYSQL_URL is not set")

    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except ModuleNotFoundError as exc:
        pytest.fail(f"MySQL driver is not installed: {exc}")
    except SQLAlchemyError as exc:
        pytest.fail(f"Could not connect using HYPOTHESIS_TEST_MYSQL_URL: {exc}")

    engine.dispose()
    yield url


def _scalar(engine: Engine, sql: str) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text(sql)).scalar() or 0)


def test_mysql_generate_populates_tables_and_respects_fks(mysql_url: str) -> None:
    suffix = uuid.uuid4().hex
    users_table = f"hypothesis_generate_users_{suffix}"
    posts_table = f"hypothesis_generate_posts_{suffix}"
    engine = create_engine(mysql_url)

    try:
        with engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {posts_table}"))
            conn.execute(text(f"DROP TABLE IF EXISTS {users_table}"))
            conn.execute(
                text(
                    f"""
                    CREATE TABLE {users_table} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        email VARCHAR(255) NOT NULL UNIQUE
                    ) ENGINE=InnoDB
                    """
                )
            )
            conn.execute(
                text(
                    f"""
                    CREATE TABLE {posts_table} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        title VARCHAR(200) NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES {users_table}(id)
                    ) ENGINE=InnoDB
                    """
                )
            )

        result = runner.invoke(
            app,
            [
                "generate",
                mysql_url,
                "--tables",
                users_table,
                "--tables",
                posts_table,
                "--rows",
                "50",
                "--seed",
                "7",
            ],
        )
        assert result.exit_code == 0, result.output

        assert _scalar(engine, f"SELECT COUNT(*) FROM {users_table}") == 50
        assert _scalar(engine, f"SELECT COUNT(*) FROM {posts_table}") == 50
        orphans = _scalar(
            engine,
            f"SELECT COUNT(*) FROM {posts_table} p "
            f"LEFT JOIN {users_table} u ON p.user_id = u.id "
            "WHERE u.id IS NULL",
        )
        assert orphans == 0
    finally:
        with engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {posts_table}"))
            conn.execute(text(f"DROP TABLE IF EXISTS {users_table}"))
        engine.dispose()
