"""``hypothesis inspect`` — display a database schema."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from hypothesis.cli.output import render_json, render_markdown, render_table
from hypothesis.core.connection_builder import build_connection_string
from hypothesis.core.exceptions import HypothesisError
from hypothesis.core.inspection import inspect_database
from hypothesis.tui.inspect_app import run_inspect_tui
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


def _connection_label(database: str, connection_string: str) -> str:
    """Return a display-safe connection label for human output."""
    if "://" not in database:
        return database
    try:
        return make_url(connection_string).render_as_string(hide_password=True)
    except Exception:  # pragma: no cover - defensive; invalid URLs fail earlier.
        return "database connection"


def _is_interactive_terminal() -> bool:
    """Whether it is appropriate to launch a full-screen TUI."""
    return sys.stdin.isatty() and sys.stdout.isatty() and os.getenv("TERM") != "dumb"


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
        str | None,
        typer.Option(
            "--format",
            "-f",
            help="Export format. Omit to open the interactive TUI.",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-V", help="Show foreign-key relationships in table output"),
    ] = False,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Config file for named connections"),
    ] = None,
) -> None:
    """Inspect a database schema and display its tables, columns, and relationships."""
    if output_format is not None and output_format not in _FORMATS:
        error_console.print(
            f"[red]Invalid --format '{output_format}'.[/red] Choose from: {', '.join(_FORMATS)}."
        )
        raise typer.Exit(code=2)
    use_tui = output_format is None
    if use_tui and not _is_interactive_terminal():
        error_console.print(
            "[red]Error:[/red] inspect opens the interactive TUI by default and requires "
            "an interactive terminal. Use --format table, --format json, or --format markdown "
            "for scripts and CI."
        )
        raise typer.Exit(code=1)

    try:
        connection_string = _resolve_connection(database, config)
        result = inspect_database(connection_string, tables=tables)
    except (HypothesisError, SQLAlchemyError, ValueError) as exc:
        error_console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if use_tui:
        run_inspect_tui(result, connection_label=_connection_label(database, connection_string))
        return

    if not result.tables:
        console.print("[yellow]No tables found in the database.[/yellow]")
        return

    if output_format == "json":
        # Plain stdout (no Rich markup) so the output stays pipe-friendly.
        print(render_json(result.tables, result.classifications))
        return
    if output_format == "markdown":
        print(render_markdown(result.tables, result.classifications))
        return

    render_table(
        result.tables, console=console, verbose=verbose, classifications=result.classifications
    )
    console.print()
    if result.cycles:
        joined = "; ".join(" ↔ ".join(cycle) for cycle in result.cycles)
        console.print(f"[yellow]Circular foreign-key dependencies detected:[/yellow] {joined}")
    else:
        console.print(f"[bold]Insertion order:[/bold] {' → '.join(result.insertion_order)}")
