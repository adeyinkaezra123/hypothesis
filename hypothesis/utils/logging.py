"""Logging setup. Secret redaction lives in :mod:`hypothesis.utils.redaction`."""

import logging

from hypothesis.utils.redaction import RedactFilter

__all__ = ["RedactFilter", "setup_logging_with_redaction"]


def setup_logging_with_redaction(
    level: str = "INFO",
    log_file: str | None = None,
    *,
    force: bool = False,
) -> None:
    """Set up logging with automatic secret redaction.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file (also redacted).
        force: Whether to replace existing root logger handlers.
    """
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RedactFilter())

    handlers: list[logging.Handler] = [console_handler]

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RedactFilter())
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        force=force,
    )
