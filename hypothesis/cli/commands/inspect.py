"""``hypothesis inspect`` — display a database schema."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from hypothesis.cli.output import render_json, render_markdown, render_table
from hypothesis.core.connection_builder import build_connection_string
from hypothesis.core.exceptions import HypothesisError
from hypothesis.core.inspector import SchemaInspector
from hypothesis.mapping.classifier import ColumnClassifier
from hypothesis.utils.redaction import register_connection_string

console = Console()
error_console = Console(stderr=True)

_FORMATS = ("table", "json", "markdown")


def _resolve_connection(database: str, config: Path | None) -> str:
    """Resolve the argument to a connection string.

    An argument containing ``://`` is treated as a connection URL; anything else
    is looked up as a named entry in a config file.
    """
    if "://" in database:
        register_connection_string(database)
        return database
    return build_connection_string(database_name=database, config_file=config)


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
) -> None:
    """Inspect a database schema and display its tables, columns, and relationships."""
    if output_format not in _FORMATS:
        error_console.print(
            f"[red]Invalid --format '{output_format}'.[/red] Choose from: {', '.join(_FORMATS)}."
        )
        raise typer.Exit(code=2)

    try:
        engine = create_engine(_resolve_connection(database, config))
        try:
            inspector = SchemaInspector(engine)
            inspector.reflect_schema(tables=tables)
            schema_tables = inspector.get_tables()
            graph = inspector.get_dependency_graph()
        finally:
            engine.dispose()
    except (HypothesisError, SQLAlchemyError, ValueError) as exc:
        error_console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if not schema_tables:
        console.print("[yellow]No tables found in the database.[/yellow]")
        return

    classifications = ColumnClassifier().classify_schema(schema_tables)

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
