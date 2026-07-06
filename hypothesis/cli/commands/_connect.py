"""Shared connection resolution and engine opening for CLI commands.

Both ``inspect`` and ``generate`` accept either a connection URL or a named
config entry, and both must fail cleanly — no traceback, no leaked DSN — on a
bad connection string or a missing database driver. That logic lives here so
the commands cannot drift apart.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import SQLAlchemyError

from hypothesis.core.connection_builder import build_connection_string
from hypothesis.core.exceptions import HypothesisError
from hypothesis.utils.redaction import register_connection_string

error_console = Console(stderr=True)


def resolve_connection(database: str, config: Path | None) -> str:
    """Resolve the CLI argument to a connection string.

    An argument containing ``://`` is treated as a connection URL (and its
    credentials are registered for log redaction); anything else is looked up
    as a named entry in a config file.
    """
    if "://" in database:
        register_connection_string(database)
        return database
    return build_connection_string(database_name=database, config_file=config)


def missing_driver_message(connection_string: str) -> str:
    """Actionable message for a missing DB driver (never includes the DSN)."""
    scheme = connection_string.split("://", 1)[0].lower()
    if "postgres" in scheme:
        return (
            "[red]Error:[/red] the PostgreSQL driver (psycopg2) is not installed.\n"
            "[dim]Install it with:[/dim] uv sync --extra postgres"
        )
    if "mysql" in scheme:
        return (
            "[red]Error:[/red] the MySQL driver (PyMySQL) is not installed.\n"
            "[dim]Install it with:[/dim] uv sync --extra mysql"
        )
    return "[red]Error:[/red] the required database driver is not installed."


def open_engine(database: str, config: Path | None) -> Engine:
    """Resolve the connection and create an engine, with friendly error messages.

    Exits cleanly (no traceback) on a bad connection string or a missing driver.
    """
    try:
        connection_string = resolve_connection(database, config)
    except (HypothesisError, ValueError) as exc:
        error_console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    try:
        return create_engine(connection_string)
    except ImportError as exc:
        error_console.print(missing_driver_message(connection_string))
        raise typer.Exit(code=1) from exc
    except (SQLAlchemyError, ValueError) as exc:
        error_console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
