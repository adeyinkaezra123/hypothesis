"""Core schema dataclasses describing reflected database structure.

These are plain data containers populated by the schema inspector and consumed
by the classification and generation layers. Field names mirror
``specs/001-core-mvp/data-model.md``; collection fields use ``default_factory``
so a table/column can be constructed incrementally.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ForeignKey:
    """A foreign key constraint linking a child column to a parent column."""

    table: str
    column: str
    referenced_table: str
    referenced_column: str
    constraint_name: str | None = None
    is_self_referential: bool = False
    on_delete: str | None = None
    on_update: str | None = None


@dataclass
class UniqueConstraint:
    """A unique constraint over one or more columns."""

    columns: list[str]
    name: str | None = None


@dataclass
class CheckConstraint:
    """A CHECK constraint.

    ``expression`` is the raw constraint text. The parsed fields
    (``min_value``/``max_value``/``allowed_values``) are populated when the
    expression matches a supported pattern; otherwise they stay ``None`` and the
    constraint is treated as unparseable.
    """

    expression: str
    name: str | None = None
    column: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: list[Any] | None = None


@dataclass
class ColumnSchema:
    """A single column within a table."""

    name: str
    table_name: str
    sql_type: str
    python_type: type
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_unique: bool = False
    is_auto_increment: bool = False
    default: Any | None = None
    enum_values: list[str] | None = None
    check_min: float | None = None
    check_max: float | None = None
    check_values: list[Any] | None = None


@dataclass
class TableSchema:
    """A reflected database table.

    Fields are reordered relative to the spec so that the only required
    positional argument is ``name``; all collections and metadata default to
    empty/``None`` and can be filled in as reflection proceeds.
    """

    name: str
    columns: list[ColumnSchema] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    foreign_keys: list[ForeignKey] = field(default_factory=list)
    unique_constraints: list[UniqueConstraint] = field(default_factory=list)
    check_constraints: list[CheckConstraint] = field(default_factory=list)
    schema: str | None = None
    is_view: bool = False
    row_count: int | None = None
