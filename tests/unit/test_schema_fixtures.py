"""Sanity checks for the SQL schema fixtures (T007).

These guard against empty or missing fixtures; the integration suite loads them
against real databases later.
"""

from pathlib import Path

import pytest

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "schemas"


@pytest.mark.parametrize(
    ("filename", "expected_tables"),
    [
        ("simple.sql", ["users", "products"]),
        ("relationships.sql", ["users", "posts", "comments"]),
        ("complex.sql", ["employees", "authors", "books", "enrollments"]),
        ("all_types.sql", ["all_types"]),
    ],
)
def test_schema_fixture_defines_expected_tables(filename: str, expected_tables: list[str]) -> None:
    path = SCHEMA_DIR / filename
    assert path.exists(), f"missing schema fixture: {filename}"
    sql = path.read_text().upper()
    assert "CREATE TABLE" in sql
    for table in expected_tables:
        assert f"CREATE TABLE {table.upper()}" in sql


def test_complex_fixture_has_self_reference() -> None:
    sql = (SCHEMA_DIR / "complex.sql").read_text()
    assert "manager_id" in sql
    assert "REFERENCES employees(id)" in sql


def test_all_types_fixture_has_enum_and_checks() -> None:
    sql = (SCHEMA_DIR / "all_types.sql").read_text().upper()
    assert "CREATE TYPE MOOD AS ENUM" in sql
    assert "CHECK" in sql
