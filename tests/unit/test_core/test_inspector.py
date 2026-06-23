"""Tests for schema reflection (SchemaInspector) against in-memory SQLite."""

from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text

from hypothesis.core.exceptions import SchemaIntrospectionError
from hypothesis.core.inspector import SchemaInspector, parse_check_constraint


@pytest.fixture
def engine() -> Iterator[Engine]:
    eng = create_engine("sqlite:///:memory:")
    with eng.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(255) NOT NULL,
                    age INTEGER CHECK (age >= 0 AND age <= 150)
                )
                """
            )
        )
        # SQLite does not reflect inline column UNIQUE; an explicit unique index is
        # the reflectable form and exercises the inspector's index-based detection.
        conn.execute(text("CREATE UNIQUE INDEX ux_users_email ON users(email)"))
        conn.execute(
            text(
                """
                CREATE TABLE posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    title VARCHAR(200) NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE employees (
                    id INTEGER PRIMARY KEY,
                    manager_id INTEGER REFERENCES employees(id)
                )
                """
            )
        )
    yield eng
    eng.dispose()


def _inspect(engine: Engine) -> SchemaInspector:
    inspector = SchemaInspector(engine)
    inspector.reflect_schema()
    return inspector


def test_reflect_lists_all_tables(engine: Engine) -> None:
    names = {t.name for t in _inspect(engine).get_tables()}
    assert {"users", "posts", "employees"} <= names


def test_columns_and_constraint_flags(engine: Engine) -> None:
    users = _inspect(engine).get_table("users")
    cols = {c.name: c for c in users.columns}
    assert cols["id"].is_primary_key is True
    assert "id" in users.primary_key
    assert cols["email"].is_unique is True
    assert cols["email"].nullable is False


def test_foreign_keys_are_extracted(engine: Engine) -> None:
    inspector = _inspect(engine)
    posts_fks = [fk for fk in inspector.get_foreign_keys() if fk.table == "posts"]
    assert posts_fks[0].referenced_table == "users"
    assert posts_fks[0].referenced_column == "id"
    posts = inspector.get_table("posts")
    assert {c.name for c in posts.columns if c.is_foreign_key} == {"user_id"}


def test_self_referential_fk_is_flagged(engine: Engine) -> None:
    fks = [fk for fk in _inspect(engine).get_foreign_keys() if fk.table == "employees"]
    assert fks[0].is_self_referential is True


def test_check_constraint_range_is_extracted(engine: Engine) -> None:
    users = _inspect(engine).get_table("users")
    age = next(c for c in users.columns if c.name == "age")
    assert age.check_min == 0
    assert age.check_max == 150


def test_insertion_order_puts_parents_first(engine: Engine) -> None:
    order = _inspect(engine).get_insertion_order()
    assert order.index("users") < order.index("posts")


def test_get_unknown_table_raises_key_error(engine: Engine) -> None:
    with pytest.raises(KeyError):
        _inspect(engine).get_table("does_not_exist")


def test_reflect_specific_tables_only(engine: Engine) -> None:
    inspector = SchemaInspector(engine)
    inspector.reflect_schema(tables=["users"])
    assert {t.name for t in inspector.get_tables()} == {"users"}


def test_reflect_missing_table_raises(engine: Engine) -> None:
    with pytest.raises(SchemaIntrospectionError):
        SchemaInspector(engine).reflect_schema(tables=["ghost"])


# -- CHECK parser (no database) --------------------------------------------


def test_parse_between() -> None:
    assert parse_check_constraint("rating BETWEEN 1 AND 5") == ("rating", 1.0, 5.0, None)


def test_parse_in_clause() -> None:
    column, low, high, values = parse_check_constraint("state IN ('open', 'closed', 'pending')")
    assert column == "state"
    assert (low, high) == (None, None)
    assert values == ["open", "closed", "pending"]


def test_parse_chained_range() -> None:
    assert parse_check_constraint("age >= 0 AND age <= 150") == ("age", 0.0, 150.0, None)


def test_parse_chained_range_uses_tightest_bounds() -> None:
    assert parse_check_constraint("age >= 18 AND age >= 21 AND age <= 100 AND age <= 65") == (
        "age",
        21.0,
        65.0,
        None,
    )


def test_parse_unparseable_returns_all_none() -> None:
    assert parse_check_constraint("json_valid(payload)") == (None, None, None, None)
