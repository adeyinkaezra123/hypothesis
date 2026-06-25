"""Tests for the BulkInserter against in-memory SQLite."""

from collections.abc import Iterator
from typing import Any

import pytest
from sqlalchemy import Engine, create_engine, text

from hypothesis.core.inserter import BulkInserter


@pytest.fixture
def engine() -> Iterator[Engine]:
    eng = create_engine("sqlite:///:memory:")
    with eng.begin() as conn:
        conn.execute(
            text("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, email VARCHAR(255) NOT NULL)")
        )
    yield eng
    eng.dispose()


def _count(engine: Engine) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0)


def test_insert_batch_writes_rows(engine: Engine) -> None:
    inserted = BulkInserter(engine).insert_batch(
        "users", [{"email": "a@x.com"}, {"email": "b@x.com"}]
    )
    assert inserted == 2
    assert _count(engine) == 2


def test_insert_batch_empty_is_noop(engine: Engine) -> None:
    assert BulkInserter(engine).insert_batch("users", []) == 0
    assert _count(engine) == 0


def test_insert_table_batches_and_reports_progress(engine: Engine) -> None:
    inserter = BulkInserter(engine, batch_size=2)
    rows = [{"email": f"u{i}@x.com"} for i in range(5)]
    calls: list[tuple[int, int]] = []

    def on_progress(done: int, total: int) -> None:
        calls.append((done, total))

    result = inserter.insert_table("users", iter(rows), total_rows=5, progress_callback=on_progress)

    assert result.rows_inserted == 5
    assert result.rows_requested == 5
    assert result.rows_skipped == 0
    assert result.rows_per_second >= 0
    assert _count(engine) == 5
    assert calls[-1] == (5, 5)  # progress reported through completion


def test_insert_table_skips_failing_batch_and_continues(engine: Engine) -> None:
    # batch_size=1 isolates the NOT NULL violation to its own batch.
    inserter = BulkInserter(engine, batch_size=1)
    rows: list[dict[str, Any]] = [{"email": "ok@x.com"}, {"email": None}, {"email": "ok2@x.com"}]
    result = inserter.insert_table("users", iter(rows), total_rows=3)

    assert result.rows_inserted == 2
    assert result.rows_skipped == 1
    assert result.errors
    assert _count(engine) == 2


def test_failing_row_in_a_batch_only_skips_that_row(engine: Engine) -> None:
    # One bad row in a multi-row batch: the good rows still land (per-row retry).
    inserter = BulkInserter(engine, batch_size=10)
    rows: list[dict[str, Any]] = [{"email": "a@x.com"}, {"email": None}, {"email": "c@x.com"}]
    result = inserter.insert_table("users", iter(rows), total_rows=3)

    assert result.rows_inserted == 2
    assert result.rows_skipped == 1
    assert _count(engine) == 2
