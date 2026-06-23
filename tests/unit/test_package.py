"""Tests for package import behavior."""

from __future__ import annotations

import importlib
import logging


def test_import_does_not_reconfigure_root_logging() -> None:
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level

    import hypothesis

    importlib.reload(hypothesis)

    assert root.handlers == original_handlers
    assert root.level == original_level


def test_public_exports_include_schema_inspector() -> None:
    import hypothesis
    from hypothesis.core.inspector import SchemaInspector

    assert hypothesis.SchemaInspector is SchemaInspector
