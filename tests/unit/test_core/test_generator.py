"""Tests for the DataGenerator."""

from typing import Any

from hypothesis.constraints.unique import UniqueConstraintHandler
from hypothesis.core.exceptions import ForeignKeyError
from hypothesis.core.generator import DataGenerator
from hypothesis.core.models import ColumnSchema, ForeignKey, TableSchema
from hypothesis.mapping.classifier import ColumnClassifier

_classifier = ColumnClassifier()


def _col(name: str, sql_type: str = "VARCHAR(255)", python_type: type = str, **kwargs: Any) -> ColumnSchema:
    return ColumnSchema(
        name=name, table_name="users", sql_type=sql_type, python_type=python_type, **kwargs
    )


def test_generate_value_for_email() -> None:
    cls = _classifier.classify_column(_col("email"))
    assert "@" in DataGenerator(seed=1).generate_value(cls)


class _FixedFkSource:
    """A fake FkValueSource returning a constant value (no DB needed)."""

    def __init__(self, value: Any) -> None:
        self.value = value

    def select_fk_value(
        self, parent_table: str, parent_column: str, distribution: str = "uniform"
    ) -> Any:
        return self.value


class _EmptyFkSource:
    """A fake FkValueSource that reports an empty parent pool."""

    def select_fk_value(
        self, parent_table: str, parent_column: str, distribution: str = "uniform"
    ) -> Any:
        raise ForeignKeyError("no parent rows")


def _posts_with_fk(*, nullable: bool) -> TableSchema:
    return TableSchema(
        name="posts",
        columns=[
            ColumnSchema("user_id", "posts", "INTEGER", int, is_foreign_key=True, nullable=nullable)
        ],
        foreign_keys=[ForeignKey("posts", "user_id", "users", "id")],
    )


def test_foreign_key_value_comes_from_the_source() -> None:
    table = _posts_with_fk(nullable=False)
    classifications = _classifier.classify_table(table)
    row = DataGenerator(seed=1).generate_row(table, classifications, fk_source=_FixedFkSource(42))
    assert row["user_id"] == 42


def test_nullable_foreign_key_with_empty_parent_is_null() -> None:
    table = _posts_with_fk(nullable=True)
    classifications = _classifier.classify_table(table)
    row = DataGenerator(seed=1).generate_row(table, classifications, fk_source=_EmptyFkSource())
    assert row["user_id"] is None


def test_generate_value_for_enum_uses_schema_values() -> None:
    cls = _classifier.classify_column(
        _col("status", sql_type="ENUM", enum_values=["draft", "active", "archived"])
    )
    assert DataGenerator(seed=1).generate_value(cls) in {"draft", "active", "archived"}


def test_generate_value_respects_check_range() -> None:
    cls = _classifier.classify_column(
        _col("age", sql_type="INTEGER", python_type=int, check_min=18, check_max=65)
    )
    for _ in range(20):
        assert 18 <= DataGenerator().generate_value(cls) <= 65


def test_post_process_is_applied() -> None:
    cls = _classifier.classify_column(_col("sku", sql_type="VARCHAR(32)"))
    value = DataGenerator(seed=1).generate_value(cls)
    assert value == value.upper()


def test_generate_row_skips_auto_increment() -> None:
    table = TableSchema(
        name="users",
        columns=[
            _col("id", sql_type="INTEGER", python_type=int, is_primary_key=True, is_auto_increment=True),
            _col("email", nullable=False),
        ],
    )
    row = DataGenerator(seed=1).generate_row(table, _classifier.classify_table(table))
    assert "id" not in row
    assert "@" in row["email"]


def test_not_null_columns_always_get_values() -> None:
    table = TableSchema(
        name="users",
        columns=[_col("email", nullable=False), _col("first_name", nullable=False)],
    )
    row = DataGenerator(seed=1).generate_row(table, _classifier.classify_table(table))
    assert row["email"] is not None
    assert row["first_name"] is not None


def test_generate_batch_count() -> None:
    table = TableSchema(name="users", columns=[_col("email", nullable=False)])
    rows = DataGenerator(seed=1).generate_batch(
        table, _classifier.classify_table(table), 7, unique_handler=UniqueConstraintHandler()
    )
    assert len(rows) == 7


def test_unique_column_yields_distinct_values() -> None:
    table = TableSchema(
        name="users", columns=[_col("email", nullable=False, is_unique=True)]
    )
    rows = DataGenerator(seed=1).generate_batch(
        table, _classifier.classify_table(table), 25, unique_handler=UniqueConstraintHandler()
    )
    emails = [row["email"] for row in rows]
    assert len(set(emails)) == len(emails)


def test_seed_makes_generation_reproducible() -> None:
    table = TableSchema(name="users", columns=[_col("first_name", nullable=False)])
    classifications = _classifier.classify_table(table)
    first = DataGenerator(seed=99).generate_row(table, classifications)
    second = DataGenerator(seed=99).generate_row(table, classifications)
    assert first == second
