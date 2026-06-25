"""Bulk insertion with batching, per-batch transactions, and progress."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import Engine, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError

from hypothesis.core.exceptions import InsertionError


@dataclass
class InsertionResult:
    """Outcome of inserting one table's rows."""

    table_name: str
    rows_requested: int
    rows_inserted: int
    rows_skipped: int
    duration_seconds: float
    rows_per_second: float
    errors: list[str] = field(default_factory=list)


class BulkInserter:
    """Inserts rows in batches using SQLAlchemy Core ``executemany``.

    Each batch runs in its own transaction, so a failure rolls back only that
    batch; preceding batches stay committed and generation continues.
    """

    def __init__(self, engine: Engine, batch_size: int = 1000) -> None:
        self.engine = engine
        self.batch_size = batch_size
        self._metadata = MetaData()
        self._tables: dict[str, Table] = {}

    def _table(self, name: str) -> Table:
        if name not in self._tables:
            self._tables[name] = Table(name, self._metadata, autoload_with=self.engine)
        return self._tables[name]

    def insert_batch(self, table_name: str, rows: list[dict[str, Any]]) -> int:
        """Insert one batch in a single transaction; return the rows written.

        Raises:
            InsertionError: if the batch fails (the transaction is rolled back).
        """
        if not rows:
            return 0
        table = self._table(table_name)
        try:
            with self.engine.begin() as conn:
                conn.execute(table.insert(), rows)
        except SQLAlchemyError as exc:
            raise InsertionError(f"Failed to insert into {table_name}: {exc}") from exc
        return len(rows)

    def insert_table(
        self,
        table_name: str,
        row_generator: Iterable[dict[str, Any]],
        total_rows: int,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> InsertionResult:
        """Insert all rows for a table in batches, reporting progress.

        A batch that fails is recorded and skipped; remaining batches continue.
        """
        start = time.perf_counter()
        inserted = 0
        skipped = 0
        errors: list[str] = []
        batch: list[dict[str, Any]] = []

        def flush() -> None:
            nonlocal inserted, skipped
            try:
                inserted += self.insert_batch(table_name, batch)
            except InsertionError as exc:
                skipped += len(batch)
                errors.append(str(exc))
            if progress_callback is not None:
                progress_callback(inserted, total_rows)

        for row in row_generator:
            batch.append(row)
            if len(batch) >= self.batch_size:
                flush()
                batch = []
        if batch:
            flush()

        duration = time.perf_counter() - start
        rate = inserted / duration if duration > 0 else 0.0
        return InsertionResult(
            table_name=table_name,
            rows_requested=total_rows,
            rows_inserted=inserted,
            rows_skipped=skipped,
            duration_seconds=duration,
            rows_per_second=rate,
            errors=errors,
        )
