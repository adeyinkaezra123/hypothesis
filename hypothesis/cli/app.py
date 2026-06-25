"""Main CLI application entry point."""

import sys
from typing import Annotated

import typer
from rich.traceback import install as install_rich_traceback

from hypothesis.cli.commands.generate import generate_command
from hypothesis.cli.commands.inspect import inspect_command
from hypothesis.cli.theme import APP_NAME, TAGLINE, brand_panel, console
from hypothesis.utils.logging import setup_logging_with_redaction

app = typer.Typer(
    name="hypothesis",
    help=TAGLINE,
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
    Hypothesis - schema-aware seed data for relational databases.
    """

    if version:
        from hypothesis import __version__

        console.print(f"[app.name]{APP_NAME}[/app.name] [success]{__version__}[/success]")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        console.print()
        console.print(brand_panel())
        console.print()
        console.print(ctx.get_help())
        raise typer.Exit()


app.command(name="inspect")(inspect_command)
app.command(name="generate")(generate_command)


def main() -> None:
    """Main entry point for the CLI.

    This function is called by the 'hypothesis' script defined in pyproject.toml.
    """
    setup_logging_with_redaction(force=True)
    install_rich_traceback(show_locals=True)
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception:
        console.print_exception(show_locals=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
