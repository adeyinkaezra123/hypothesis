"""Tests for the Textual inspect app."""

from __future__ import annotations

import asyncio

from textual.widgets import DataTable, Input, ListView, Static

from hypothesis.core.inspection import InspectionResult
from hypothesis.tui.inspect_app import InspectApp


def test_inspect_app_boots_and_renders_summary_at_80x24(sample_result: InspectionResult) -> None:
    async def run() -> None:
        app = InspectApp(sample_result, connection_label="sqlite:///schema.db")
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            summary = str(app.query_one("#summary", Static).content)
            assert "2 tables" in summary
            assert "5 columns" in summary
            assert len(app.query_one("#table-list", ListView).children) == 2

    asyncio.run(run())


def test_table_selection_updates_column_and_detail_views(sample_result: InspectionResult) -> None:
    async def run() -> None:
        app = InspectApp(sample_result, connection_label="sqlite:///schema.db")
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()
            details = str(app.query_one("#details", Static).content)
            assert "Table: posts" in details
            assert "Foreign keys: user_id -> users.id" in details

    asyncio.run(run())


def test_search_filters_tables_and_escape_clears_search(sample_result: InspectionResult) -> None:
    async def run() -> None:
        app = InspectApp(sample_result, connection_label="sqlite:///schema.db")
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("/")
            await pilot.press("p", "o")
            await pilot.pause()
            assert app.query_one("#search", Input).value == "po"
            assert len(app.query_one("#table-list", ListView).children) == 1

            await pilot.press("escape")
            await pilot.pause()
            assert app.query_one("#search", Input).value == ""
            assert len(app.query_one("#table-list", ListView).children) == 2

    asyncio.run(run())


def test_low_confidence_toggle_limits_visible_columns(sample_result: InspectionResult) -> None:
    async def run() -> None:
        app = InspectApp(sample_result, connection_label="sqlite:///schema.db")
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("down")  # highlight posts (arrow nav, j/k removed)
            await pilot.press("f")
            await pilot.pause()
            table = app.query_one("#columns", DataTable)
            details = str(app.query_one("#details", Static).content)
            assert table.row_count == 1
            assert "Filter: low-confidence columns only" in details

    asyncio.run(run())


def test_help_screen_opens_and_escape_returns(sample_result: InspectionResult) -> None:
    async def run() -> None:
        app = InspectApp(sample_result, connection_label="sqlite:///schema.db")
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("shift+slash")
            await pilot.pause()
            assert app.screen.query_one("#help-panel", Static)
            await pilot.press("escape")
            await pilot.pause()
            assert not app.screen.query("#help-panel")

    asyncio.run(run())


def test_quit_binding_exits_cleanly(sample_result: InspectionResult) -> None:
    async def run() -> None:
        app = InspectApp(sample_result, connection_label="sqlite:///schema.db")
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("q")

    asyncio.run(run())


def test_enter_on_column_opens_classification_detail(sample_result: InspectionResult) -> None:
    async def run() -> None:
        app = InspectApp(sample_result, connection_label="sqlite:///schema.db")
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("down")  # highlight posts
            await pilot.press("enter")  # select posts -> focus the columns table
            await pilot.press("down", "down")  # move cursor to the "title" row
            await pilot.press("enter")  # open that column's detail
            await pilot.pause()
            detail = str(app.screen.query_one("#column-detail", Static).content)
            assert "title" in detail
            assert "type_fallback" in detail
            assert "needs review" in detail

            await pilot.press("escape")
            await pilot.pause()
            assert not app.screen.query("#column-detail")

    asyncio.run(run())
