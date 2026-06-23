"""Tests for the core schema dataclasses."""

from hypothesis.core.models import (
    CheckConstraint,
    ColumnSchema,
    ForeignKey,
    TableSchema,
    UniqueConstraint,
)


def _column(name: str = "id") -> ColumnSchema:
    return ColumnSchema(name=name, table_name="users", sql_type="INTEGER", python_type=int)


def test_table_minimal_construction() -> None:
    table = TableSchema(name="users")
    assert table.name == "users"
    assert table.columns == []
    assert table.primary_key == []
    assert table.foreign_keys == []
    assert table.is_view is False
    assert table.schema is None
    assert table.row_count is None


def test_table_default_collections_are_isolated() -> None:
    first = TableSchema(name="a")
    second = TableSchema(name="b")
    first.columns.append(_column())
    assert first.columns != second.columns
    assert second.columns == []


def test_column_defaults() -> None:
    col = ColumnSchema(name="email", table_name="users", sql_type="VARCHAR(255)", python_type=str)
    assert col.nullable is True
    assert col.is_primary_key is False
    assert col.is_foreign_key is False
    assert col.length is None
    assert col.enum_values is None


def test_foreign_key_defaults() -> None:
    fk = ForeignKey(
        table="posts", column="user_id", referenced_table="users", referenced_column="id"
    )
    assert fk.is_self_referential is False
    assert fk.constraint_name is None


def test_self_referential_foreign_key() -> None:
    fk = ForeignKey(
        table="employees",
        column="manager_id",
        referenced_table="employees",
        referenced_column="id",
        is_self_referential=True,
    )
    assert fk.is_self_referential is True


def test_unique_constraint() -> None:
    uc = UniqueConstraint(columns=["email"])
    assert uc.columns == ["email"]
    assert uc.name is None


def test_check_constraint_unparsed_by_default() -> None:
    ck = CheckConstraint(expression="age >= 18")
    assert ck.expression == "age >= 18"
    assert ck.min_value is None
    assert ck.max_value is None
    assert ck.allowed_values is None
