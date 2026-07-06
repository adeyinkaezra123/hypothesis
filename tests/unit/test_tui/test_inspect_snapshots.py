"""Visual snapshot tests for the inspect TUI.

These render the app to SVG and compare against committed baselines, so a
restyle that changes the look is caught without coupling assertions to exact
on-screen wording. Regenerate baselines after an intentional change with:

    uv run pytest tests/unit/test_tui --snapshot-update
"""

from __future__ import annotations

from typing import Any

from hypothesis.core.inspection import InspectionResult
from hypothesis.tui.inspect_app import InspectApp

_SIZE = (120, 36)
_LABEL = "postgresql://localhost/hypothesis_test"


def test_snapshot_main_view(snap_compare: Any, sample_result: InspectionResult) -> None:
    app = InspectApp(sample_result, connection_label=_LABEL)
    assert snap_compare(app, terminal_size=_SIZE)


def test_snapshot_low_confidence_filter(
    snap_compare: Any, sample_result: InspectionResult
) -> None:
    app = InspectApp(sample_result, connection_label=_LABEL)
    assert snap_compare(app, terminal_size=_SIZE, press=["down", "f"])


def test_snapshot_column_detail(snap_compare: Any, sample_result: InspectionResult) -> None:
    app = InspectApp(sample_result, connection_label=_LABEL)
    assert snap_compare(
        app, terminal_size=_SIZE, press=["down", "enter", "down", "down", "enter"]
    )
