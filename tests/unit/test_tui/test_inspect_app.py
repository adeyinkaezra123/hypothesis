"""Tests for the Textual inspect app."""

from __future__ import annotations

import asyncio

from textual.widgets import DataTable, Input, ListView, Static

from hypothesis.core.graph import DependencyGraph
from hypothesis.core.inspection import InspectionResult, InspectionSummary
from hypothesis.core.models import ColumnSchema, ForeignKey, TableSchema
from hypothesis.mapping.types import ClassificationResult, SemanticType
from hypothesis.tui.inspect_app import InspectApp


def _classification(
    column: ColumnSchema,
    semantic_type: SemanticType,
    *,
    confidence: float = 0.9,
    needs_review: bool = False,
) -> ClassificationResult:
    return ClassificationResult(
        column=column,
        semantic_type=semantic_type,
        confidence=confidence,
        faker_provider="word",
        matched_layer=2,
        needs_review=needs_review,
    )


def _sample_result() -> InspectionResult:
    user_id = ColumnSchema(
        "id",
        "users",
        "INTEGER",
        int,
        nullable=False,
        is_primary_key=True,
        is_auto_increment=True,
    )
    email = ColumnSchema("email", "users", "VARCHAR(255)", str, nullable=False, is_unique=True)
    post_id = ColumnSchema("id", "posts", "INTEGER", int, nullable=False, is_primary_key=True)
    user_fk = ColumnSchema(
        "user_id",
        "posts",
        "INTEGER",
        int,
        nullable=False,
        is_foreign_key=True,
    )
    title = ColumnSchema("title", "posts", "VARCHAR(200)", str)
    users = TableSchema(
        name="users",
        columns=[user_id, email],
        primary_key=["id"],
    )
    posts = TableSchema(
        name="posts",
        columns=[post_id, user_fk, title],
        primary_key=["id"],
        foreign_keys=[ForeignKey("posts", "user_id", "users", "id")],
    )
    graph = DependencyGraph(["users", "posts"])
    graph.build_from_foreign_keys(posts.foreign_keys)
    classifications = {
        "users": {
            "id": _classification(user_id, SemanticType.ID),
            "email": _classification(email, SemanticType.EMAIL),
        },
        "posts": {
            "id": _classification(post_id, SemanticType.ID),
            "user_id": _classification(user_fk, SemanticType.FOREIGN_KEY),
            "title": _classification(
                title,
                SemanticType.TYPE_FALLBACK,
                confidence=0.4,
                needs_review=True,
            ),
        },
    }
    return InspectionResult(
        tables=[users, posts],
        classifications=classifications,
        graph=graph,
        insertion_order=["users", "posts"],
        cycles=[],
        summary=InspectionSummary(
            table_count=2,
            column_count=5,
            foreign_key_count=1,
            low_confidence_count=1,
        ),
    )


def test_inspect_app_boots_and_renders_summary_at_80x24() -> None:
    async def run() -> None:
        app = InspectApp(_sample_result(), connection_label="sqlite:///schema.db")
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            summary = str(app.query_one("#summary", Static).content)
            assert "2 tables" in summary
            assert "5 columns" in summary
            assert len(app.query_one("#table-list", ListView).children) == 2

    asyncio.run(run())


def test_table_selection_updates_column_and_detail_views() -> None:
    async def run() -> None:
        app = InspectApp(_sample_result(), connection_label="sqlite:///schema.db")
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()
            details = str(app.query_one("#details", Static).content)
            assert "Table: posts" in details
            assert "Foreign keys: user_id -> users.id" in details

    asyncio.run(run())


def test_search_filters_tables_and_escape_clears_search() -> None:
    async def run() -> None:
        app = InspectApp(_sample_result(), connection_label="sqlite:///schema.db")
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


def test_low_confidence_toggle_limits_visible_columns() -> None:
    async def run() -> None:
        app = InspectApp(_sample_result(), connection_label="sqlite:///schema.db")
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("j")
            await pilot.press("f")
            await pilot.pause()
            table = app.query_one("#columns", DataTable)
            details = str(app.query_one("#details", Static).content)
            assert table.row_count == 1
            assert "Filter: low-confidence columns only" in details

    asyncio.run(run())


def test_help_screen_opens_and_escape_returns() -> None:
    async def run() -> None:
        app = InspectApp(_sample_result(), connection_label="sqlite:///schema.db")
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("shift+slash")
            await pilot.pause()
            assert app.screen.query_one("#help-panel", Static)
            await pilot.press("escape")
            await pilot.pause()
            assert not app.screen.query("#help-panel")

    asyncio.run(run())


def test_quit_binding_exits_cleanly() -> None:
    async def run() -> None:
        app = InspectApp(_sample_result(), connection_label="sqlite:///schema.db")
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("q")

    asyncio.run(run())
