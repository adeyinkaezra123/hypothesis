"""PostgreSQL integration tests for the generate CLI.

These tests require a real PostgreSQL URL and are skipped by default:

- HYPOTHESIS_TEST_POSTGRES_URL=postgresql://...
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


def _scalar(engine: Engine, sql: str) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text(sql)).scalar() or 0)


# Database-generated primary keys come in two flavours. SERIAL accepts an
# explicit value; GENERATED ALWAYS AS IDENTITY rejects one outright. Generation
# must let the database fill both, so we exercise the strict case too.
_PK_DDL = {
    "serial": "SERIAL PRIMARY KEY",
    "identity": "INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY",
}


@pytest.mark.parametrize("pk_ddl", list(_PK_DDL.values()), ids=list(_PK_DDL))
def test_postgres_generate_populates_tables_and_respects_fks(
    postgres_url: str, pk_ddl: str
) -> None:
    suffix = uuid.uuid4().hex
    users_table = f"hypothesis_generate_users_{suffix}"
    posts_table = f"hypothesis_generate_posts_{suffix}"
    engine = create_engine(postgres_url)

    try:
        with engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {posts_table}"))
            conn.execute(text(f"DROP TABLE IF EXISTS {users_table}"))
            conn.execute(
                text(
                    f"""
                    CREATE TABLE {users_table} (
                        id {pk_ddl},
                        email VARCHAR(255) NOT NULL UNIQUE
                    )
                    """
                )
            )
            conn.execute(
                text(
                    f"""
                    CREATE TABLE {posts_table} (
                        id {pk_ddl},
                        user_id INTEGER NOT NULL REFERENCES {users_table}(id),
                        title VARCHAR(200) NOT NULL
                    )
                    """
                )
            )

        result = runner.invoke(
            app,
            [
                "generate",
                postgres_url,
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
