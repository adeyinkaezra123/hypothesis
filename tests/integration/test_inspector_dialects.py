"""Dialect integration tests for SchemaInspector.

These tests require real database URLs and are skipped by default:

- HYPOTHESIS_TEST_POSTGRES_URL=postgresql://...
- HYPOTHESIS_TEST_MYSQL_URL=mysql://...
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from hypothesis.core.inspector import SchemaInspector

ENUM_VALUES = ["draft", "active", "archived"]


def _engine_from_env(env_var: str) -> Iterator[Engine]:
    url = os.getenv(env_var)
    if not url:
        pytest.skip(f"{env_var} is not set")

    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except ModuleNotFoundError as exc:
        pytest.fail(f"Database driver for {env_var} is not installed: {exc}")
    except SQLAlchemyError as exc:
        pytest.fail(f"Could not connect using {env_var}: {exc}")

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def postgres_engine() -> Iterator[Engine]:
    yield from _engine_from_env("HYPOTHESIS_TEST_POSTGRES_URL")


@pytest.fixture
def mysql_engine() -> Iterator[Engine]:
    yield from _engine_from_env("HYPOTHESIS_TEST_MYSQL_URL")


def test_postgres_enum_values_are_reflected(postgres_engine: Engine) -> None:
    suffix = uuid.uuid4().hex
    enum_name = f"hypothesis_status_{suffix}"
    table_name = f"hypothesis_enum_pg_{suffix}"

    try:
        with postgres_engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            conn.execute(text(f"DROP TYPE IF EXISTS {enum_name}"))
            conn.execute(text(f"CREATE TYPE {enum_name} AS ENUM ('draft', 'active', 'archived')"))
            conn.execute(
                text(
                    f"""
                    CREATE TABLE {table_name} (
                        id SERIAL PRIMARY KEY,
                        status {enum_name} NOT NULL
                    )
                    """
                )
            )
        inspector = SchemaInspector(postgres_engine)
        inspector.reflect_schema(tables=[table_name])
        status = next(
            col for col in inspector.get_table(table_name).columns if col.name == "status"
        )
        assert status.enum_values == ENUM_VALUES
    finally:
        with postgres_engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            conn.execute(text(f"DROP TYPE IF EXISTS {enum_name}"))


def test_mysql_enum_values_are_reflected(mysql_engine: Engine) -> None:
    table_name = f"hypothesis_enum_mysql_{uuid.uuid4().hex}"

    try:
        with mysql_engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            conn.execute(
                text(
                    f"""
                    CREATE TABLE {table_name} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        status ENUM('draft', 'active', 'archived') NOT NULL
                    )
                    """
                )
            )
        inspector = SchemaInspector(mysql_engine)
        inspector.reflect_schema(tables=[table_name])
        status = next(
            col for col in inspector.get_table(table_name).columns if col.name == "status"
        )
        assert status.enum_values == ENUM_VALUES
    finally:
        with mysql_engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
