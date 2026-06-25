"""Shared terminal theme and small output helpers."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

APP_NAME = "Hypothesis"
TAGLINE = "Schema-aware seed data for PostgreSQL and MySQL."

THEME = Theme(
    {
        "app.name": "bold cyan",
        "app.tagline": "dim",
        "heading": "bold cyan",
        "muted": "dim",
        "success": "green",
        "warning": "yellow",
        "error": "bold red",
        "accent": "cyan",
        "table.header": "bold cyan",
        "table.metric": "bold white",
    }
)

console = Console(theme=THEME)
error_console = Console(stderr=True, theme=THEME)


def status(label: str, detail: str, *, style: str = "success") -> str:
    """Return a compact status line."""
    marker = "✓" if style == "success" else "!"
    return (
        f"[{style}]{marker}[/{style}] [table.metric]{label}[/table.metric] [muted]{detail}[/muted]"
    )


def error_message(title: str, detail: str | None = None) -> str:
    """Return a consistently styled error message."""
    if detail:
        return f"[error]Error:[/error] {title}\n[muted]{detail}[/muted]"
    return f"[error]Error:[/error] {title}"


def brand_panel() -> Panel:
    """No-command app introduction."""
    body = (
        f"[app.name]{APP_NAME}[/app.name]\n"
        f"[app.tagline]{TAGLINE}[/app.tagline]\n\n"
        "[muted]Try:[/muted] hypothesis inspect postgresql://user@localhost/app\n"
        "[muted]Next:[/muted] hypothesis generate postgresql://user@localhost/app --rows 100"
    )
    return Panel.fit(body, border_style="accent", padding=(1, 2))
