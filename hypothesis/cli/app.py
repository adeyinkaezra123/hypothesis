"""Main CLI application entry point."""

import os
import sys
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.traceback import install as install_rich_traceback

from hypothesis.cli.commands.generate import generate_command
from hypothesis.cli.commands.inspect import inspect_command
from hypothesis.config.parser import ConfigParser
from hypothesis.utils import redaction
from hypothesis.utils.logging import setup_logging_with_redaction

console = Console()

app = typer.Typer(
    name="hypothesis",
    help="Semantic database seeder - generate realistic fake data for PostgreSQL and MySQL",
    add_completion=True,
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def common_options(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            is_eager=True,
        ),
    ] = False,
) -> None:
    """
    Hypothesis - Semantic Database Seeder

    Generate realistic fake data for your databases automatically.
    """

    if version:
        from hypothesis import __version__

        console.print(f"[bold cyan]hypothesis[/bold cyan] version [green]{__version__}[/green]")
        raise typer.Exit()

    # If no subcommand is given, show banner + help
    if ctx.invoked_subcommand is None:
        console.print()
        console.print(
            Panel.fit(
                "[bold cyan]hypothesis[/bold cyan]\n"
                "Semantic database seeder for PostgreSQL and MySQL\n\n"
                "[dim]Automatically generate realistic fake data based on schema introspection[/dim]",
                border_style="cyan",
            )
        )
        console.print()
        console.print(ctx.get_help())
        raise typer.Exit()


app.command(name="inspect")(inspect_command)
app.command(name="generate")(generate_command)


def _apply_redaction_settings() -> None:
    """Apply secret-redaction options from the dotfile config (.hypothesisrc)."""
    redaction.configure(redaction.settings_from_mapping(ConfigParser().config))


def main() -> None:
    """Main entry point for the CLI.

    This function is called by the 'hypothesis' script defined in pyproject.toml.
    """
    setup_logging_with_redaction(force=True)
    _apply_redaction_settings()
    # Don't dump frame locals by default: a connection DSN (with password) is
    # often sitting in them. Opt in with HYPOTHESIS_DEBUG=1 when debugging.
    show_locals = os.getenv("HYPOTHESIS_DEBUG") == "1"
    install_rich_traceback(show_locals=show_locals)
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception:
        console.print_exception(show_locals=show_locals)
        sys.exit(1)


if __name__ == "__main__":
    main()
