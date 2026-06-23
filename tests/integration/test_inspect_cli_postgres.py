"""PostgreSQL integration tests for the inspect CLI.

These tests require a real PostgreSQL URL and are skipped by default:

- HYPOTHESIS_TEST_POSTGRES_URL=postgresql://...
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from typer.testing import CliRunner

from hypothesis.cli.app import app

runner = CliRunner()


@pytest.fixture
def postgres_url() -> Iterator[str]:
    url = os.getenv("HYPOTHESIS_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("HYPOTHESIS_TEST_POSTGRES_URL is not set")

    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except ModuleNotFoundError as exc:
        pytest.fail(f"PostgreSQL driver is not installed: {exc}")
    except SQLAlchemyError as exc:
        pytest.fail(f"Could not connect using HYPOTHESIS_TEST_POSTGRES_URL: {exc}")

    engine.dispose()
    yield url


def test_postgres_inspect_cli_outputs_schema_and_foreign_keys(postgres_url: str) -> None:
    suffix = uuid.uuid4().hex
    users_table = f"hypothesis_inspect_users_{suffix}"
    posts_table = f"hypothesis_inspect_posts_{suffix}"
    engine = create_engine(postgres_url)

    try:
        with engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {posts_table}"))
            conn.execute(text(f"DROP TABLE IF EXISTS {users_table}"))
            conn.execute(
                text(
                    f"""
                    CREATE TABLE {users_table} (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) NOT NULL UNIQUE
                    )
                    """
                )
            )
            conn.execute(
                text(
                    f"""
                    CREATE TABLE {posts_table} (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES {users_table}(id),
                        title VARCHAR(200) NOT NULL
                    )
                    """
                )
            )

        result = runner.invoke(
            app,
            [
                "inspect",
                postgres_url,
                "--tables",
                users_table,
                "--tables",
                posts_table,
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0, result.output

        data = json.loads(result.output)
        tables = {table["name"]: table for table in data}
        assert set(tables) == {users_table, posts_table}
        assert tables[users_table]["primary_key"] == ["id"]
        assert tables[posts_table]["foreign_keys"] == [
            {
                "column": "user_id",
                "references": f"{users_table}.id",
                "self_referential": False,
            }
        ]
    finally:
        with engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {posts_table}"))
            conn.execute(text(f"DROP TABLE IF EXISTS {users_table}"))
        engine.dispose()
