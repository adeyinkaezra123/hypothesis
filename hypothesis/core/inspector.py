"""Database schema reflection via SQLAlchemy."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import Engine
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.engine import Inspector
from sqlalchemy.exc import SQLAlchemyError

from hypothesis.core.exceptions import SchemaIntrospectionError
from hypothesis.core.graph import DependencyGraph
from hypothesis.core.models import (
    CheckConstraint,
    ColumnSchema,
    ForeignKey,
    TableSchema,
    UniqueConstraint,
)

_BETWEEN_RE = re.compile(
    r"(\w+)\s+BETWEEN\s+(-?\d+(?:\.\d+)?)\s+AND\s+(-?\d+(?:\.\d+)?)", re.IGNORECASE
)
_IN_RE = re.compile(r"(\w+)\s+IN\s*\(([^)]+)\)", re.IGNORECASE)
_COMPARE_RE = re.compile(r"(\w+)\s*(>=|<=|>|<)\s*(-?\d+(?:\.\d+)?)")


def parse_check_constraint(
    expression: str,
) -> tuple[str | None, float | None, float | None, list[str] | None]:
    """Best-effort extraction of ``(column, min, max, allowed_values)`` from a CHECK.

    Handles the common forms ``col BETWEEN a AND b``, ``col IN (...)``, and chained
    ``col >= a AND col <= b`` comparisons. Anything else yields all ``None`` and is
    treated as unparseable (the caller falls back to type-based generation).
    """
    text = expression.replace("`", "").replace('"', "")

    between = _BETWEEN_RE.search(text)
    if between:
        return between.group(1), float(between.group(2)), float(between.group(3)), None

    in_match = _IN_RE.search(text)
    if in_match:
        values = [value.strip().strip("'") for value in in_match.group(2).split(",")]
        return in_match.group(1), None, None, values

    min_value: float | None = None
    max_value: float | None = None
    column: str | None = None
    for match in _COMPARE_RE.finditer(text):
        column = match.group(1)
        number = float(match.group(3))
        if match.group(2) in (">=", ">"):
            min_value = number if min_value is None else max(min_value, number)
        else:
            max_value = number if max_value is None else min(max_value, number)
    if column is not None:
        return column, min_value, max_value, None

    return None, None, None, None


class SchemaInspector:
    """Reflects a database schema into Hypothesis's data model."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._inspector: Inspector = sa_inspect(engine)
        self._tables: dict[str, TableSchema] = {}

    def reflect_schema(
        self,
        tables: list[str] | None = None,
        include_views: bool = False,
    ) -> None:
        """Reflect the schema into :class:`TableSchema` objects.

        Args:
            tables: Specific tables to reflect, or ``None`` for all.
            include_views: Whether to include views (skipped by default).

        Raises:
            SchemaIntrospectionError: if reflection fails or a requested table
                does not exist.
        """
        try:
            base_tables = list(self._inspector.get_table_names())
            view_names = list(self._inspector.get_view_names()) if include_views else []
            available = base_tables + view_names

            if tables is not None:
                missing = sorted(set(tables) - set(available))
                if missing:
                    raise SchemaIntrospectionError(
                        f"Tables not found in database: {', '.join(missing)}"
                    )
                targets = [name for name in available if name in set(tables)]
            else:
                targets = available

            views = set(view_names)
            self._tables = {
                name: self._reflect_table(name, is_view=name in views) for name in targets
            }
        except SQLAlchemyError as exc:
            raise SchemaIntrospectionError(f"Schema reflection failed: {exc}") from exc

    def get_tables(self) -> list[TableSchema]:
        """Return all reflected tables."""
        return list(self._tables.values())

    def get_table(self, name: str) -> TableSchema:
        """Return a specific reflected table.

        Raises:
            KeyError: if the table was not reflected.
        """
        if name not in self._tables:
            raise KeyError(f"Table not reflected: {name}")
        return self._tables[name]

    def get_foreign_keys(self) -> list[ForeignKey]:
        """Return every foreign key across all reflected tables."""
        return [fk for table in self._tables.values() for fk in table.foreign_keys]

    def get_dependency_graph(self) -> DependencyGraph:
        """Build a dependency graph from the reflected foreign keys."""
        graph = DependencyGraph(tables=list(self._tables.keys()))
        graph.build_from_foreign_keys(self.get_foreign_keys())
        return graph

    def get_insertion_order(self) -> list[str]:
        """Return table names in topological (parents-first) insertion order."""
        return self.get_dependency_graph().topological_sort()

    # -- internal reflection helpers ----------------------------------------

    def _reflect_table(self, name: str, *, is_view: bool) -> TableSchema:
        columns_info = self._inspector.get_columns(name)
        pk_columns = list(self._inspector.get_pk_constraint(name).get("constrained_columns") or [])
        foreign_keys = self._build_foreign_keys(name)
        fk_columns = {fk.column for fk in foreign_keys}

        unique_constraints = [
            UniqueConstraint(columns=list(uc["column_names"]), name=uc.get("name"))
            for uc in self._inspector.get_unique_constraints(name)
            if uc.get("column_names")
        ]
        single_unique = {uc.columns[0] for uc in unique_constraints if len(uc.columns) == 1}
        for index in self._inspector.get_indexes(name):
            index_columns = [col for col in (index.get("column_names") or []) if col is not None]
            if index.get("unique") and len(index_columns) == 1:
                single_unique.add(index_columns[0])

        check_constraints, checks_by_column = self._build_checks(name)

        columns = [
            self._build_column(
                name,
                col,
                is_pk=col["name"] in pk_columns,
                is_fk=col["name"] in fk_columns,
                is_unique=col["name"] in single_unique,
                check=checks_by_column.get(col["name"]),
            )
            for col in columns_info
        ]

        return TableSchema(
            name=name,
            columns=columns,
            primary_key=pk_columns,
            foreign_keys=foreign_keys,
            unique_constraints=unique_constraints,
            check_constraints=check_constraints,
            is_view=is_view,
        )

    def _build_foreign_keys(self, table: str) -> list[ForeignKey]:
        foreign_keys: list[ForeignKey] = []
        for fk in self._inspector.get_foreign_keys(table):
            referred_table = fk["referred_table"]
            options = fk.get("options") or {}
            for child_col, parent_col in zip(fk["constrained_columns"], fk["referred_columns"]):
                foreign_keys.append(
                    ForeignKey(
                        table=table,
                        column=child_col,
                        referenced_table=referred_table,
                        referenced_column=parent_col,
                        constraint_name=fk.get("name"),
                        is_self_referential=referred_table == table,
                        on_delete=options.get("ondelete"),
                        on_update=options.get("onupdate"),
                    )
                )
        return foreign_keys

    def _build_checks(self, table: str) -> tuple[list[CheckConstraint], dict[str, CheckConstraint]]:
        try:
            raw_checks = self._inspector.get_check_constraints(table)
        except (NotImplementedError, SQLAlchemyError):
            return [], {}

        constraints: list[CheckConstraint] = []
        by_column: dict[str, CheckConstraint] = {}
        for check in raw_checks:
            sqltext = str(check.get("sqltext") or "")
            column, low, high, values = parse_check_constraint(sqltext)
            constraint = CheckConstraint(
                expression=sqltext,
                name=check.get("name"),
                column=column,
                min_value=low,
                max_value=high,
                allowed_values=values,
            )
            constraints.append(constraint)
            if column is not None:
                by_column[column] = constraint
        return constraints, by_column

    def _build_column(
        self,
        table: str,
        col: Any,
        *,
        is_pk: bool,
        is_fk: bool,
        is_unique: bool,
        check: CheckConstraint | None,
    ) -> ColumnSchema:
        col_type = col["type"]
        try:
            python_type: type = col_type.python_type
        except (NotImplementedError, AttributeError):
            python_type = str
        enum_values = getattr(col_type, "enums", None)

        return ColumnSchema(
            name=col["name"],
            table_name=table,
            sql_type=str(col_type),
            python_type=python_type,
            length=getattr(col_type, "length", None),
            precision=getattr(col_type, "precision", None),
            scale=getattr(col_type, "scale", None),
            nullable=bool(col.get("nullable", True)),
            is_primary_key=is_pk,
            is_foreign_key=is_fk,
            is_unique=is_unique,
            is_auto_increment=bool(col.get("autoincrement", False)),
            default=col.get("default"),
            enum_values=list(enum_values) if enum_values else None,
            check_min=check.min_value if check else None,
            check_max=check.max_value if check else None,
            check_values=check.allowed_values if check else None,
        )
