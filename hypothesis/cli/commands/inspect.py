"""``hypothesis inspect`` — display a database schema."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from sqlalchemy.exc import SQLAlchemyError

from hypothesis.cli.commands._connect import open_engine
from hypothesis.cli.output import render_explanation, render_json, render_markdown, render_table
from hypothesis.core.exceptions import HypothesisError
from hypothesis.core.inspector import SchemaInspector
from hypothesis.mapping.classifier import ColumnClassifier

console = Console()
error_console = Console(stderr=True)

_FORMATS = ("table", "json", "markdown")


def inspect_command(
    database: Annotated[
        str,
        typer.Argument(help="Connection string (postgresql://...) or a named config entry"),
    ],
    tables: Annotated[
        list[str] | None,
        typer.Option("--tables", "-t", help="Restrict to specific tables (repeatable)"),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: table, json, or markdown"),
    ] = "table",
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-V", help="Show foreign-key relationships"),
    ] = False,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Config file for named connections"),
    ] = None,
    explain: Annotated[
        str | None,
        typer.Option(
            "--explain",
            help="Explain one column's classification as TABLE.COLUMN (overrides --format)",
        ),
    ] = None,
) -> None:
    """Inspect a database schema and display its tables, columns, and relationships."""
    if output_format not in _FORMATS:
        error_console.print(
            f"[red]Invalid --format '{output_format}'.[/red] Choose from: {', '.join(_FORMATS)}."
        )
        raise typer.Exit(code=2)

    explain_table = explain_column = ""
    if explain is not None:
        explain_table, dot, explain_column = explain.partition(".")
        if not dot or not explain_table or not explain_column:
            error_console.print("[red]--explain expects TABLE.COLUMN[/red] (e.g. users.email).")
            raise typer.Exit(code=2)

    engine = open_engine(database, config)
    try:
        inspector = SchemaInspector(engine)
        inspector.reflect_schema(tables=[explain_table] if explain_table else tables)
        schema_tables = inspector.get_tables()
        graph = inspector.get_dependency_graph()
    except (HypothesisError, SQLAlchemyError, ValueError) as exc:
        error_console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    finally:
        engine.dispose()

    if not schema_tables:
        console.print("[yellow]No tables found in the database.[/yellow]")
        return

    classifications = ColumnClassifier().classify_schema(schema_tables)

    if explain_table and explain_column:
        table_schema = next((t for t in schema_tables if t.name == explain_table), None)
        if table_schema is None:
            error_console.print(f"[red]Error:[/red] table '{explain_table}' not found.")
            raise typer.Exit(code=1)
        column = next((c for c in table_schema.columns if c.name == explain_column), None)
        if column is None:
            available = ", ".join(c.name for c in table_schema.columns)
            error_console.print(
                f"[red]Error:[/red] column '{explain_column}' not found in table "
                f"'{explain_table}'. Available: {available}"
            )
            raise typer.Exit(code=1)
        classification = classifications.get(explain_table, {}).get(explain_column)
        render_explanation(table_schema, column, classification, console=console)
        return

    if output_format == "json":
        # Plain stdout (no Rich markup) so the output stays pipe-friendly.
        print(render_json(schema_tables, classifications))
        return
    if output_format == "markdown":
        print(render_markdown(schema_tables, classifications))
        return

    render_table(schema_tables, console=console, verbose=verbose, classifications=classifications)
    console.print()
    cycles = graph.detect_cycles()
    if cycles:
        joined = "; ".join(" ↔ ".join(cycle) for cycle in cycles)
        console.print(f"[yellow]Circular foreign-key dependencies detected:[/yellow] {joined}")
    else:
        console.print(f"[bold]Insertion order:[/bold] {' → '.join(graph.topological_sort())}")

    flagged = [
        (table_name, column_name, result)
        for table_name, columns in classifications.items()
        for column_name, result in columns.items()
        if result.needs_review
    ]
    if flagged:
        summary = ", ".join(
            f"{t}.{c} ({r.semantic_type.value} {r.confidence:.2f})" for t, c, r in flagged
        )
        console.print()
        console.print(f"[yellow]⚠ {len(flagged)} column(s) need review:[/yellow] {summary}")
        console.print(
            "[dim]Run 'hypothesis inspect <db> --explain TABLE.COLUMN' "
            "to see the classification reasoning.[/dim]"
        )
