"""Textual schema browser for ``hypothesis inspect``."""

from __future__ import annotations

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import DataTable, Footer, Header, Input, Label, ListItem, ListView, Static

from hypothesis.cli.output import constraint_flags
from hypothesis.core.inspection import InspectionResult
from hypothesis.core.models import ColumnSchema, TableSchema
from hypothesis.mapping.types import ClassificationResult

# A cohesive palette (Catppuccin Macchiato-derived) registered as a theme, so
# every surface tints from one place and `border: round $accent` etc. stay
# consistent across the app and its modals.
HYPOTHESIS_THEME = Theme(
    name="hypothesis",
    primary="#8aadf4",  # blue   — structure, focus rings
    secondary="#8bd5ca",  # teal   — SQL types
    accent="#c6a0f6",  # mauve  — titles, highlights, modal borders
    success="#a6da95",  # green  — confident classifications
    warning="#eed49f",  # amber  — needs review
    error="#ed8796",  # red    — cycles / problems
    foreground="#cad3f5",
    background="#1e2030",
    surface="#24273a",
    panel="#2a2d44",
    dark=True,
)


def _palette(theme: Theme | None) -> dict[str, str]:
    """Rich style strings derived from the *active* theme.

    DataTable cells and ``Text`` content take Rich styles, not Textual ``$``
    variables, so the colours are read from the theme here rather than
    hardcoded. That keeps confidence/type colouring in step with a theme switch
    (Ctrl+P) and lets it adapt to light or dark backgrounds. ``muted`` stays the
    Rich ``dim`` attribute, which dims whatever the theme's text colour is.
    """
    if theme is None:  # pragma: no cover - defensive; a theme is always set.
        return {
            "ok": "green",
            "review": "yellow",
            "error": "red",
            "type": "cyan",
            "key": "blue",
            "accent": "magenta",
            "muted": "dim",
        }
    return {
        "ok": theme.success or "green",
        "review": theme.warning or "yellow",
        "error": theme.error or "red",
        "type": theme.secondary or "cyan",
        "key": theme.primary,
        "accent": theme.accent or theme.primary,
        "muted": "dim",
    }


class InspectHelpScreen(ModalScreen[None]):
    """Keyboard help overlay."""

    BINDINGS = [("escape", "dismiss", "Close"), ("q", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        p = _palette(self.app.get_theme(self.app.theme))
        body = Text()
        body.append("Hypothesis Inspect\n\n", style=f"bold {p['review']}")
        for key, desc in (
            ("Up / Down", "Move between tables"),
            ("Enter", "Open the table, then a column's detail"),
            ("/", "Search tables"),
            ("f", "Toggle low-confidence columns"),
            ("?", "Show this help"),
            ("Esc", "Clear search or close"),
            ("q", "Quit"),
        ):
            body.append(f"{key:<16}", style=f"bold {p['key']}")
            body.append(f"{desc}\n")
        body.append(
            "\nUse --format table, --format json, or --format markdown for\n"
            "scripts, CI, and exported output.",
            style=p["muted"],
        )
        yield Static(body, id="help-panel")


class ColumnDetailScreen(ModalScreen[None]):
    """Full classification detail for a single column.

    Surfaces the parts of :class:`ClassificationResult` the summary table has no
    room for: the matched layer/pattern, the Faker provider, and the reasoning.
    """

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
        ("enter", "dismiss", "Close"),
    ]

    def __init__(self, column: ColumnSchema, classification: ClassificationResult | None) -> None:
        super().__init__()
        self._column = column
        self._classification = classification

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="column-detail-scroll"):
            yield Static(self._detail(), id="column-detail")

    def _detail(self) -> Text:
        column = self._column
        result = self._classification
        p = _palette(self.app.get_theme(self.app.theme))
        body = Text()
        body.append(f"{column.name}\n", style=f"bold {p['accent']}")
        body.append(column.sql_type, style=p["type"])
        body.append(
            f"  ·  {'nullable' if column.nullable else 'not null'}\n\n", style=p["muted"]
        )

        flags = constraint_flags(column)
        if flags:
            self._field(body, "Constraints", flags, p)
        if result is None:
            body.append("No classification available for this column.", style=p["muted"])
            body.append("\n\nEsc to close", style=p["muted"])
            return body

        self._field(body, "Semantic", result.semantic_type.value, p)
        mark = "needs review" if result.needs_review else "confident"
        confidence = Text(
            f"{result.confidence:.2f}  {mark}",
            style=p["review"] if result.needs_review else p["ok"],
        )
        self._field(body, "Confidence", confidence, p)
        self._field(body, "Match layer", str(result.matched_layer), p)
        if result.matched_pattern:
            self._field(body, "Pattern", result.matched_pattern, p)
        provider = result.faker_provider
        if result.faker_kwargs:
            provider += f"  {result.faker_kwargs}"
        self._field(body, "Faker", provider, p)
        if result.reasoning:
            body.append("\n")
            body.append(result.reasoning, style=f"italic {p['muted']}")
        body.append("\n\nEsc to close", style=p["muted"])
        return body

    @staticmethod
    def _field(body: Text, label: str, value: str | Text, palette: dict[str, str]) -> None:
        body.append(f"{label:<13} ", style=f"bold {palette['key']}")
        body.append(value if isinstance(value, Text) else Text(value))
        body.append("\n")


class InspectApp(App[None]):
    """Interactive schema browser for a completed inspection result."""

    TITLE = "Hypothesis Inspect"
    SUB_TITLE = "schema browser"
    CSS_PATH = "inspect_app.tcss"
    ENABLE_COMMAND_PALETTE = True
    low_confidence_only: reactive[bool] = reactive(False)
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("/", "focus_search", "Search"),
        ("f", "toggle_low_confidence", "Low confidence"),
        Binding("question_mark", "show_help", "Help", key_display="?", priority=True),
        Binding("shift+slash", "show_help", "Help", show=False, priority=True),
        ("escape", "clear_search", "Back"),
    ]

    def __init__(self, result: InspectionResult, *, connection_label: str) -> None:
        super().__init__()
        self.result = result
        self.connection_label = connection_label
        self.filtered_tables = list(result.tables)
        self.selected_table: TableSchema | None = result.tables[0] if result.tables else None

    def _palette(self) -> dict[str, str]:
        return _palette(self.get_theme(self.theme))

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(self._summary_text(), id="summary")
        if not self.result.tables:
            yield Static("No tables found in the database.", id="empty")
            yield Footer()
            return
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Static("TABLES", classes="pane-title")
                yield Input(placeholder="Search tables", id="search")
                yield ListView(id="table-list")
            with Vertical(id="main"):
                yield Static("COLUMNS", classes="pane-title")
                yield DataTable(id="columns", zebra_stripes=True)
                yield Static("DETAILS", classes="pane-title")
                with VerticalScroll(id="details-scroll"):
                    yield Static(id="details")
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(HYPOTHESIS_THEME)
        self.theme = "hypothesis"
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
        # Enter on a table selects it and drops focus into the columns table, so
        # a second Enter opens that column's detail (Enter, Enter to drill in).
        self._select_table_by_name(event.item.name)
        self.query_one("#columns", DataTable).focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Open the full classification detail for the chosen column."""
        if self.selected_table is None:
            return
        column_name = event.row_key.value
        column = next(
            (col for col in self.selected_table.columns if col.name == column_name), None
        )
        if column is None:
            return
        classifications = self.result.classifications.get(self.selected_table.name, {})
        self.push_screen(ColumnDetailScreen(column, classifications.get(column.name)))

    def action_focus_search(self) -> None:
        self.query_one("#search", Input).focus()

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

    def _summary_text(self) -> Text:
        summary = self.result.summary
        visible = len(self.filtered_tables)
        total = len(self.result.tables)
        filter_state = "review only" if self.low_confidence_only else "all columns"
        p = self._palette()
        text = Text()
        text.append(f"{self.connection_label}\n", style=f"bold {p['key']}")
        text.append(f"{summary.table_count} tables", style="bold")
        text.append("  ·  ", style=p["muted"])
        text.append(f"{summary.column_count} columns", style="bold")
        text.append("  ·  ", style=p["muted"])
        text.append(f"{summary.foreign_key_count} foreign keys")
        text.append("  ·  ", style=p["muted"])
        review_style = p["review"] if summary.low_confidence_count else p["muted"]
        text.append(f"{summary.low_confidence_count} need review", style=review_style)
        text.append("  ·  ", style=p["muted"])
        text.append(f"{visible}/{total} visible · {filter_state}", style=p["muted"])
        return text

    def _refresh_summary(self) -> None:
        self.query_one("#summary", Static).update(self._summary_text())

    def _rebuild_table_list(self) -> None:
        table_list = self.query_one("#table-list", ListView)
        table_list.clear()
        for table in self.filtered_tables:
            table_list.append(ListItem(Label(self._table_list_label(table)), name=table.name))
        table_list.index = 0 if self.filtered_tables else None
        self._refresh_summary()

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

        p = self._palette()
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
                Text(column.name, style="bold"),
                Text(column.sql_type, style=p["type"]),
                Text("✓" if column.nullable else "—", style=p["muted"]),
                Text(constraint_flags(column), style=p["key"]),
                self._semantic_text(classification, p),
                self._confidence_text(classification, p),
                key=column.name,
            )

        details.update(self._detail_text(self.selected_table, visible_columns, classifications))

    def _detail_text(
        self,
        table: TableSchema,
        visible_columns: list[ColumnSchema],
        classifications: dict[str, ClassificationResult],
    ) -> Text:
        p = self._palette()
        text = Text()
        self._detail_field(text, "Table", self._qualified_table_name(table), p["key"])
        self._detail_field(
            text, "Columns shown", f"{len(visible_columns)} of {len(table.columns)}", p["key"]
        )
        if self.low_confidence_only:
            text.append("Filter: low-confidence columns only\n", style=p["review"])
        if table.primary_key:
            self._detail_field(text, "Primary key", ", ".join(table.primary_key), p["key"])
        if table.foreign_keys:
            fks = ", ".join(
                f"{fk.column} -> {fk.referenced_table}.{fk.referenced_column}"
                for fk in table.foreign_keys
            )
            self._detail_field(text, "Foreign keys", fks, p["key"])
        needs_review = [name for name, result in classifications.items() if result.needs_review]
        if needs_review:
            self._detail_field(
                text, "Needs review", ", ".join(needs_review), p["key"], value_style=p["review"]
            )
        else:
            self._detail_field(text, "Needs review", "none", p["key"], value_style=p["muted"])
        if self.result.cycles:
            cycle_text = "; ".join(" <-> ".join(cycle) for cycle in self.result.cycles)
            self._detail_field(text, "Cycle warning", cycle_text, p["error"])
        elif self.result.insertion_order:
            self._detail_field(
                text, "Insertion order", ", ".join(self.result.insertion_order), p["key"]
            )
        text.append("\nEnter on a column for full classification detail", style=p["muted"])
        return text

    @staticmethod
    def _detail_field(
        text: Text,
        label: str,
        value: str,
        key_style: str,
        *,
        value_style: str = "",
    ) -> None:
        text.append(f"{label}: ", style=f"bold {key_style}")
        text.append(f"{value}\n", style=value_style)

    def _table_list_label(self, table: TableSchema) -> Text:
        review_count = sum(
            1
            for result in self.result.classifications.get(table.name, {}).values()
            if result.needs_review
        )
        p = self._palette()
        parts = [f"{len(table.columns)} cols"]
        if table.foreign_keys:
            parts.append(f"{len(table.foreign_keys)} FK")
        label = Text()
        label.append(self._qualified_table_name(table), style="bold")
        label.append("\n")
        label.append("  ·  ".join(parts), style=p["muted"])
        if review_count:
            label.append("  ·  ", style=p["muted"])
            label.append(f"{review_count} review", style=p["review"])
        return label

    @staticmethod
    def _semantic_text(classification: ClassificationResult | None, palette: dict[str, str]) -> Text:
        if classification is None:
            return Text("")
        style = palette["muted"] if classification.needs_review else ""
        return Text(classification.semantic_type.value, style=style)

    @staticmethod
    def _confidence_text(
        classification: ClassificationResult | None, palette: dict[str, str]
    ) -> Text:
        if classification is None:
            return Text("")
        if classification.needs_review:
            return Text(f"{classification.confidence:.2f} ⚠", style=palette["review"])
        return Text(f"{classification.confidence:.2f} ✓", style=palette["ok"])

    @staticmethod
    def _qualified_table_name(table: TableSchema) -> str:
        return f"{table.schema}.{table.name}" if table.schema else table.name


def run_inspect_tui(result: InspectionResult, *, connection_label: str) -> None:
    """Launch the inspect TUI."""
    InspectApp(result, connection_label=connection_label).run()
