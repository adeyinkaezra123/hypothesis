"""Rich output formatters for schema display.

Three renderers back the ``inspect`` command's ``--format`` flag:
``table`` (Rich, default, interactive), ``json`` (machine-readable), and
``markdown`` (documentation-ready). JSON and Markdown return strings;
the table renderer prints to a Rich console.

Each renderer optionally takes ``classifications`` (table name -> column name ->
:class:`ClassificationResult`); when present, columns show their inferred
semantic type and a colour-coded confidence (✓ high, ⚠ needs review).
:func:`render_explanation` prints the full classification card for one column
(backing ``inspect --explain``).
"""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.table import Table

from hypothesis.core.models import ColumnSchema, TableSchema
from hypothesis.mapping.types import ClassificationResult

ClassificationMap = dict[str, dict[str, ClassificationResult]]


def constraint_flags(col: ColumnSchema) -> str:
    """Compact human-readable constraint summary for a column."""
    flags: list[str] = []
    if col.is_primary_key:
        flags.append("PK")
    if col.is_foreign_key:
        flags.append("FK")
    if col.is_unique:
        flags.append("unique")
    if col.is_auto_increment:
        flags.append("auto")
    if not col.nullable:
        flags.append("not null")
    if col.enum_values:
        flags.append(f"enum({len(col.enum_values)})")
    return ", ".join(flags)


def _qualified_name(table: TableSchema) -> str:
    name = f"{table.schema}.{table.name}" if table.schema else table.name
    return f"{name} (view)" if table.is_view else name


def _semantic_cell(result: ClassificationResult | None) -> str:
    """Semantic type, review indicator, and confidence for Markdown cells."""
    if result is None:
        return ""
    indicator = "✓" if not result.needs_review else "⚠"
    return f"{result.semantic_type.value} {indicator} {result.confidence:.2f}"


def _confidence_cell(result: ClassificationResult | None) -> str:
    """Colour-coded confidence with a review indicator for the table renderer."""
    if result is None:
        return ""
    if result.needs_review:
        return f"[yellow]{result.confidence:.2f} ⚠[/yellow]"
    return f"[green]{result.confidence:.2f} ✓[/green]"


def render_table(
    tables: list[TableSchema],
    *,
    console: Console | None = None,
    verbose: bool = False,
    classifications: ClassificationMap | None = None,
) -> None:
    """Render schemas as Rich tables to the console."""
    console = console or Console()
    show_semantic = classifications is not None
    for table in tables:
        results = classifications.get(table.name, {}) if classifications else {}
        rich_table = Table(title=_qualified_name(table), title_justify="left")
        rich_table.add_column("Column", style="cyan", no_wrap=True)
        rich_table.add_column("Type", style="green")
        rich_table.add_column("Null", justify="center")
        rich_table.add_column("Constraints", style="yellow")
        if show_semantic:
            rich_table.add_column("Semantic", style="magenta")
            rich_table.add_column("Confidence")
        for col in table.columns:
            cells = [
                col.name,
                col.sql_type,
                "✓" if col.nullable else "—",
                constraint_flags(col),
            ]
            if show_semantic:
                result = results.get(col.name)
                cells.append(result.semantic_type.value if result else "")
                cells.append(_confidence_cell(result))
            rich_table.add_row(*cells)
        console.print(rich_table)

        if verbose and table.foreign_keys:
            console.print("  [dim]Foreign keys:[/dim]")
            for fk in table.foreign_keys:
                marker = " [dim](self)[/dim]" if fk.is_self_referential else ""
                console.print(
                    f"    {fk.column} → {fk.referenced_table}.{fk.referenced_column}{marker}"
                )


def render_explanation(
    table: TableSchema,
    column: ColumnSchema,
    classification: ClassificationResult | None,
    *,
    console: Console | None = None,
) -> None:
    """Print the full classification card for one column.

    Surfaces what the summary table has no room for: the matched layer and
    pattern, the Faker provider, and the classifier's reasoning. Plain-friendly:
    Rich drops the colour when output is piped.
    """
    console = console or Console()

    def field(label: str, value: str) -> None:
        console.print(f"[bold blue]{label:<12}[/bold blue] {value}")

    console.print(f"[bold cyan]{_qualified_name(table)}.{column.name}[/bold cyan]")
    nullability = "nullable" if column.nullable else "not null"
    console.print(f"[green]{column.sql_type}[/green] [dim]·[/dim] {nullability}")
    console.print()
    flags = constraint_flags(column)
    if flags:
        field("Constraints", flags)
    if classification is None:
        console.print("[dim]No classification available for this column.[/dim]")
        return
    field("Semantic", classification.semantic_type.value)
    if classification.needs_review:
        field("Confidence", f"{classification.confidence:.2f} [yellow]⚠ needs review[/yellow]")
    else:
        field("Confidence", f"{classification.confidence:.2f} [green]✓[/green]")
    field("Match layer", str(classification.matched_layer))
    if classification.matched_pattern:
        field("Pattern", classification.matched_pattern)
    provider = classification.faker_provider
    if classification.faker_kwargs:
        provider += f" {classification.faker_kwargs}"
    field("Faker", provider)
    if classification.reasoning:
        field("Reasoning", classification.reasoning)


def _column_to_dict(
    col: ColumnSchema, classification: ClassificationResult | None
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": col.name,
        "sql_type": col.sql_type,
        "python_type": getattr(col.python_type, "__name__", str(col.python_type)),
        "nullable": col.nullable,
        "primary_key": col.is_primary_key,
        "foreign_key": col.is_foreign_key,
        "unique": col.is_unique,
        "auto_increment": col.is_auto_increment,
        "default": col.default,
        "enum_values": col.enum_values,
        "length": col.length,
        "precision": col.precision,
        "scale": col.scale,
        "check_min": col.check_min,
        "check_max": col.check_max,
        "check_values": col.check_values,
    }
    if classification is not None:
        data["semantic_type"] = classification.semantic_type.value
        data["confidence"] = round(classification.confidence, 2)
        data["needs_review"] = classification.needs_review
    return data


def _table_to_dict(table: TableSchema, results: dict[str, ClassificationResult]) -> dict[str, Any]:
    return {
        "name": table.name,
        "schema": table.schema,
        "is_view": table.is_view,
        "row_count": table.row_count,
        "primary_key": table.primary_key,
        "columns": [_column_to_dict(c, results.get(c.name)) for c in table.columns],
        "foreign_keys": [
            {
                "column": fk.column,
                "references": f"{fk.referenced_table}.{fk.referenced_column}",
                "self_referential": fk.is_self_referential,
            }
            for fk in table.foreign_keys
        ],
        "unique_constraints": [uc.columns for uc in table.unique_constraints],
    }


def render_json(tables: list[TableSchema], classifications: ClassificationMap | None = None) -> str:
    """Serialize schemas to a JSON string."""
    classifications = classifications or {}
    payload = [_table_to_dict(t, classifications.get(t.name, {})) for t in tables]
    return json.dumps(payload, indent=2, default=str)


def render_markdown(
    tables: list[TableSchema], classifications: ClassificationMap | None = None
) -> str:
    """Render schemas as Markdown tables."""
    show_semantic = classifications is not None
    classifications = classifications or {}
    lines: list[str] = []
    for table in tables:
        results = classifications.get(table.name, {})
        lines.append(f"## {_qualified_name(table)}")
        lines.append("")
        if show_semantic:
            lines.append("| Column | Type | Nullable | Constraints | Semantic |")
            lines.append("| --- | --- | --- | --- | --- |")
        else:
            lines.append("| Column | Type | Nullable | Constraints |")
            lines.append("| --- | --- | --- | --- |")
        for col in table.columns:
            nullable = "yes" if col.nullable else "no"
            row = f"| {col.name} | {col.sql_type} | {nullable} | {constraint_flags(col)} |"
            if show_semantic:
                row += f" {_semantic_cell(results.get(col.name))} |"
            lines.append(row)
        if table.foreign_keys:
            lines.append("")
            lines.append("**Foreign keys:**")
            for fk in table.foreign_keys:
                lines.append(f"- `{fk.column}` → `{fk.referenced_table}.{fk.referenced_column}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
