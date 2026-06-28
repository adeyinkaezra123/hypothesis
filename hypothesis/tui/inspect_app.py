"""Textual schema browser for ``hypothesis inspect``."""

from __future__ import annotations

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Input, Label, ListItem, ListView, Static

from hypothesis.cli.output import constraint_flags
from hypothesis.core.inspection import InspectionResult
from hypothesis.core.models import ColumnSchema, TableSchema
from hypothesis.mapping.types import ClassificationResult


class InspectHelpScreen(ModalScreen[None]):
    """Keyboard help overlay."""

    BINDINGS = [("escape", "dismiss", "Close"), ("q", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        yield Static(
            "\n".join(
                [
                    "Hypothesis Inspect",
                    "",
                    "Up/Down or j/k   Move between tables",
                    "Enter           Focus column table",
                    "/               Search tables",
                    "f               Toggle low-confidence columns",
                    "?               Show this help",
                    "Esc             Clear search or close help",
                    "q               Quit",
                    "",
                    "Use --format table, --format json, or --format markdown for",
                    "scripts, CI, and exported output.",
                ]
            ),
            id="help-panel",
        )


class InspectApp(App[None]):
    """Interactive schema browser for a completed inspection result."""

    TITLE = "Hypothesis Inspect"
    SUB_TITLE = "Schema browser"
    ENABLE_COMMAND_PALETTE = True
    low_confidence_only: reactive[bool] = reactive(False)
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("/", "focus_search", "Search"),
        ("f", "toggle_low_confidence", "Low confidence"),
        Binding("question_mark", "show_help", "Help", key_display="?", priority=True),
        Binding("shift+slash", "show_help", "Help", show=False, priority=True),
        ("escape", "clear_search", "Back"),
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("enter", "focus_columns", "Columns"),
    ]
    CSS = """
    Screen {
        layout: vertical;
    }

    #summary {
        height: 4;
        padding: 1 2;
        content-align: left middle;
        border-bottom: tall $surface;
        background: $panel;
    }

    #body {
        height: 1fr;
    }

    .pane-title {
        height: 3;
        padding: 1 1 0 1;
        text-style: bold;
        color: $text;
        background: $surface;
    }

    #sidebar {
        width: 34;
        min-width: 24;
        border-right: tall $surface;
        background: $panel;
    }

    #search {
        height: 3;
        margin: 0 1 1 1;
    }

    #table-list {
        height: 1fr;
        padding: 0 1 1 1;
    }

    ListItem {
        height: 2;
    }

    ListItem Label {
        padding: 0 1;
    }

    #main {
        width: 1fr;
        background: $background;
    }

    #columns {
        height: 2fr;
        min-height: 10;
        margin: 0 1 1 1;
    }

    #details {
        height: 1fr;
        min-height: 8;
        margin: 0 1 1 1;
        padding: 1 2;
        border: tall $surface;
        background: $panel;
    }

    #empty {
        padding: 2;
    }

    #help-panel {
        width: 70;
        max-width: 90%;
        height: auto;
        max-height: 90%;
        padding: 1 2;
        border: thick $primary;
        background: $surface;
    }
    """

    def __init__(self, result: InspectionResult, *, connection_label: str) -> None:
        super().__init__()
        self.result = result
        self.connection_label = connection_label
        self.filtered_tables = list(result.tables)
        self.selected_table: TableSchema | None = result.tables[0] if result.tables else None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(self._summary_text(), id="summary")
        if not self.result.tables:
            yield Static("No tables found in the database.", id="empty")
            yield Footer()
            return
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Static("Tables", classes="pane-title")
                yield Input(placeholder="Search tables", id="search")
                yield ListView(id="table-list")
            with Vertical(id="main"):
                yield Static("Columns", classes="pane-title")
                yield DataTable(id="columns", zebra_stripes=True)
                yield Static("Details", classes="pane-title")
                yield Static(id="details")
        yield Footer()

    def on_mount(self) -> None:
        if self.result.tables:
            self._rebuild_table_list()
            self._render_selected_table()
            self.set_focus(self.query_one("#table-list", ListView))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search":
            return
        query = event.value.casefold().strip()
        self.filtered_tables = [
            table
            for table in self.result.tables
            if query in self._qualified_table_name(table).casefold()
        ]
        self.selected_table = self.filtered_tables[0] if self.filtered_tables else None
        self._rebuild_table_list()
        self._render_selected_table()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        table_name = event.item.name if event.item else None
        self._select_table_by_name(table_name)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._select_table_by_name(event.item.name)

    async def on_key(self, event: events.Key) -> None:
        if event.key in {"question_mark", "shift+slash"}:
            event.stop()
            await self.action_show_help()

    def action_focus_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_focus_columns(self) -> None:
        self.query_one("#columns", DataTable).focus()

    def action_cursor_down(self) -> None:
        table_list = self.query_one("#table-list", ListView)
        table_list.action_cursor_down()
        self._sync_selected_table_from_list()

    def action_cursor_up(self) -> None:
        table_list = self.query_one("#table-list", ListView)
        table_list.action_cursor_up()
        self._sync_selected_table_from_list()

    def action_toggle_low_confidence(self) -> None:
        self.low_confidence_only = not self.low_confidence_only
        self._refresh_summary()
        self._render_selected_table()

    async def action_show_help(self) -> None:
        await self.push_screen(InspectHelpScreen())

    def action_clear_search(self) -> None:
        search = self.query_one("#search", Input)
        if search.value:
            search.value = ""
            self.filtered_tables = list(self.result.tables)
            self.selected_table = self.filtered_tables[0] if self.filtered_tables else None
            self._rebuild_table_list()
            self._render_selected_table()
            self._refresh_summary()
            return
        self.set_focus(self.query_one("#table-list", ListView))

    def _summary_text(self) -> str:
        summary = self.result.summary
        visible = len(self.filtered_tables)
        total = len(self.result.tables)
        filter_state = "review only" if self.low_confidence_only else "all columns"
        return (
            f"{self.connection_label}\n"
            f"{summary.table_count} tables | {summary.column_count} columns | "
            f"{summary.foreign_key_count} foreign keys | "
            f"{summary.low_confidence_count} need review | "
            f"{visible}/{total} visible | {filter_state}"
        )

    def _refresh_summary(self) -> None:
        self.query_one("#summary", Static).update(self._summary_text())

    def _rebuild_table_list(self) -> None:
        table_list = self.query_one("#table-list", ListView)
        table_list.clear()
        for table in self.filtered_tables:
            label = self._table_list_label(table)
            table_list.append(ListItem(Label(label), name=table.name))
        table_list.index = 0 if self.filtered_tables else None
        self._refresh_summary()

    def _sync_selected_table_from_list(self) -> None:
        table_list = self.query_one("#table-list", ListView)
        index = table_list.index
        if index is None or index >= len(self.filtered_tables):
            self.selected_table = None
        else:
            self.selected_table = self.filtered_tables[index]
        self._render_selected_table()

    def _select_table_by_name(self, table_name: str | None) -> None:
        self.selected_table = next(
            (table for table in self.filtered_tables if table.name == table_name),
            None,
        )
        self._render_selected_table()

    def _render_selected_table(self) -> None:
        columns = self.query_one("#columns", DataTable)
        details = self.query_one("#details", Static)
        columns.clear(columns=True)
        columns.add_columns("Column", "Type", "Null", "Constraints", "Semantic", "Confidence")
        columns.cursor_type = "row"

        if self.selected_table is None:
            details.update("No matching tables.\nPress Esc to clear search.")
            return

        classifications = self.result.classifications.get(self.selected_table.name, {})
        visible_columns = [
            column
            for column in self.selected_table.columns
            if not self.low_confidence_only
            or classifications.get(column.name) is not None
            and classifications[column.name].needs_review
        ]
        for column in visible_columns:
            classification = classifications.get(column.name)
            columns.add_row(
                column.name,
                column.sql_type,
                "yes" if column.nullable else "no",
                constraint_flags(column),
                classification.semantic_type.value if classification else "",
                self._confidence_label(classification),
                key=column.name,
            )

        details.update(self._detail_text(self.selected_table, visible_columns, classifications))

    def _detail_text(
        self,
        table: TableSchema,
        visible_columns: list[ColumnSchema],
        classifications: dict[str, ClassificationResult],
    ) -> str:
        lines = [
            f"Table: {self._qualified_table_name(table)}",
            f"Columns shown: {len(visible_columns)} of {len(table.columns)}",
        ]
        if self.low_confidence_only:
            lines.append("Filter: low-confidence columns only")
        if table.primary_key:
            lines.append(f"Primary key: {', '.join(table.primary_key)}")
        if table.foreign_keys:
            fks = ", ".join(
                f"{fk.column} -> {fk.referenced_table}.{fk.referenced_column}"
                for fk in table.foreign_keys
            )
            lines.append(f"Foreign keys: {fks}")
        needs_review = [name for name, result in classifications.items() if result.needs_review]
        if needs_review:
            lines.append(f"Needs review: {', '.join(needs_review)}")
        else:
            lines.append("Needs review: none")
        if self.result.cycles:
            cycle_text = "; ".join(" <-> ".join(cycle) for cycle in self.result.cycles)
            lines.append(f"Cycle warning: {cycle_text}")
        elif self.result.insertion_order:
            lines.append(f"Insertion order: {', '.join(self.result.insertion_order)}")
        lines.append("Navigation: / search, f review filter, ? help, q quit")
        return "\n".join(lines)

    def _table_list_label(self, table: TableSchema) -> str:
        relationship_count = len(table.foreign_keys)
        review_count = sum(
            1
            for result in self.result.classifications.get(table.name, {}).values()
            if result.needs_review
        )
        name = self._qualified_table_name(table)
        parts = [f"{len(table.columns)} cols"]
        if relationship_count:
            parts.append(f"{relationship_count} FK")
        if review_count:
            parts.append(f"{review_count} review")
        return f"{name}\n  {'  '.join(parts)}"

    @staticmethod
    def _qualified_table_name(table: TableSchema) -> str:
        return f"{table.schema}.{table.name}" if table.schema else table.name

    @staticmethod
    def _confidence_label(classification: ClassificationResult | None) -> str:
        if classification is None:
            return ""
        label = "review" if classification.needs_review else "ok"
        return f"{classification.confidence:.2f} {label}"


def run_inspect_tui(result: InspectionResult, *, connection_label: str) -> None:
    """Launch the inspect TUI."""
    InspectApp(result, connection_label=connection_label).run()
