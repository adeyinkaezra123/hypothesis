"""``hypothesis generate`` — generate and insert fake data."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table as RichTable
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from hypothesis.constraints.foreign_keys import ForeignKeyResolver
from hypothesis.constraints.unique import UniqueConstraintHandler
from hypothesis.core.connection_builder import build_connection_string
from hypothesis.core.exceptions import HypothesisError
from hypothesis.core.generator import DataGenerator
from hypothesis.core.inserter import BulkInserter, InsertionResult
from hypothesis.core.inspector import SchemaInspector
from hypothesis.core.models import TableSchema
from hypothesis.mapping.classifier import ColumnClassifier

console = Console()
error_console = Console(stderr=True)


def _resolve_connection(database: str, config: Path | None) -> str:
    if "://" in database:
        return database
    return build_connection_string(database_name=database, config_file=config)


def _build_fk_cache(table: TableSchema, resolver: ForeignKeyResolver) -> dict[str, list[Any]]:
    """Cache valid parent ids for each foreign key (parents are inserted first)."""
    cache: dict[str, list[Any]] = {}
    for fk in table.foreign_keys:
        cache[f"{table.name}.{fk.column}"] = resolver.cache_parent_ids(
            fk.referenced_table, fk.referenced_column
        )
    return cache


def _make_progress() -> Progress:
    return Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("{task.completed}/{task.total} rows"),
        TimeElapsedColumn(),
        console=console,
    )


def _progress_callback(progress: Progress, task_id: TaskID) -> Callable[[int, int], None]:
    def callback(done: int, _total: int) -> None:
        progress.update(task_id, completed=done)

    return callback


def _print_summary(results: list[InsertionResult]) -> None:
    summary = RichTable(title="Generation summary", title_justify="left")
    summary.add_column("Table", style="cyan")
    summary.add_column("Inserted", justify="right", style="green")
    summary.add_column("Skipped", justify="right", style="yellow")
    summary.add_column("Rows/sec", justify="right")
    total = 0
    for result in results:
        total += result.rows_inserted
        summary.add_row(
            result.table_name,
            str(result.rows_inserted),
            str(result.rows_skipped),
            f"{result.rows_per_second:,.0f}",
        )
    console.print(summary)
    console.print(
        f"[bold green]Inserted {total:,} rows across {len(results)} table(s).[/bold green]"
    )


def generate_command(
    database: Annotated[
        str, typer.Argument(help="Connection string (postgresql://...) or a named config entry")
    ],
    rows: Annotated[int, typer.Option("--rows", "-r", help="Rows to generate per table")] = 1000,
    tables: Annotated[
        list[str] | None,
        typer.Option("--tables", "-t", help="Restrict to specific tables (repeatable)"),
    ] = None,
    batch_size: Annotated[
        int, typer.Option("--batch-size", help="Rows per insert batch")
    ] = 1000,
    locale: Annotated[str, typer.Option("--locale", help="Faker locale")] = "en_US",
    seed: Annotated[
        int | None, typer.Option("--seed", help="Random seed for reproducible output")
    ] = None,
    config: Annotated[
        Path | None, typer.Option("--config", "-c", help="Config file for named connections")
    ] = None,
) -> None:
    """Generate and insert fake data, respecting foreign keys and unique constraints."""
    if rows < 1:
        error_console.print("[red]--rows must be at least 1.[/red]")
        raise typer.Exit(code=2)

    try:
        engine = create_engine(_resolve_connection(database, config))
    except (HypothesisError, SQLAlchemyError, ValueError) as exc:
        error_console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    try:
        inspector = SchemaInspector(engine)
        inspector.reflect_schema(tables=tables)
        schema_tables = {table.name: table for table in inspector.get_tables()}
        if not schema_tables:
            console.print("[yellow]No tables found to populate.[/yellow]")
            return
        insertion_order = inspector.get_insertion_order()
        classifications = ColumnClassifier().classify_schema(list(schema_tables.values()))

        generator = DataGenerator(faker_locale=locale, seed=seed)
        inserter = BulkInserter(engine, batch_size=batch_size)
        resolver = ForeignKeyResolver(engine)

        results: list[InsertionResult] = []
        with _make_progress() as progress:
            for table_name in insertion_order:
                table = schema_tables[table_name]
                table_classifications = classifications[table_name]
                fk_cache = _build_fk_cache(table, resolver)
                unique_handler = UniqueConstraintHandler()
                task_id = progress.add_task(table_name, total=rows)
                row_iter = (
                    generator.generate_row(table, table_classifications, fk_cache, unique_handler)
                    for _ in range(rows)
                )
                results.append(
                    inserter.insert_table(
                        table_name, row_iter, rows, _progress_callback(progress, task_id)
                    )
                )
    except (HypothesisError, SQLAlchemyError) as exc:
        error_console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    finally:
        engine.dispose()

    _print_summary(results)
