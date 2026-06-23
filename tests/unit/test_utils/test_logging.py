"""Tests for logging redaction utilities."""

from __future__ import annotations

import logging
from io import StringIO

from hypothesis.utils.logging import RedactFilter, setup_logging_with_redaction


def test_redact_filter_masks_connection_url_password() -> None:
    credential = "fixture_credential"
    url = "postgresql://user" + ":" + credential + "@example.test/db"
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=f"Connecting to {url}",
        args=(),
        exc_info=None,
    )

    RedactFilter().filter(record)

    assert credential not in str(record.msg)
    assert "postgresql://user:" + "***" + "@example.test/db" in str(record.msg)


def test_setup_logging_respects_existing_handlers_by_default() -> None:
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    root.handlers = [handler]

    try:
        setup_logging_with_redaction()

        assert root.handlers == [handler]
    finally:
        root.handlers = original_handlers
        root.setLevel(original_level)


def test_setup_logging_can_force_redacting_handler() -> None:
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level

    try:
        setup_logging_with_redaction(force=True)

        assert root.handlers
        assert any(
            isinstance(filter_, RedactFilter)
            for handler in root.handlers
            for filter_ in handler.filters
        )
    finally:
        root.handlers = original_handlers
        root.setLevel(original_level)
