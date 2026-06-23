"""Logging utilities with automatic secret redaction."""

import logging
import re
from typing import Any


class RedactFilter(logging.Filter):
    """Filter that redacts sensitive information from log messages.

    Automatically redacts:
    - Passwords in connection strings (user:<password>@host)
    - Common secret patterns (API keys, tokens, passwords)
    - Values from sensitive config keys
    """

    # Patterns to redact
    PATTERNS: list[tuple[re.Pattern[str], str]] = [
        # Connection strings: user:<password>@host -> user:***@host
        (re.compile(r"://([^:]+):([^@\s]+)@"), r"://\1:***@"),
        # password=value or password='value' or password="value"
        (re.compile(r"(password\s*=\s*['\"]?)([^'\"\s]+)(['\"]?)", re.IGNORECASE), r"\1***\3"),
        # API keys, tokens, secrets (key=value format)
        (
            re.compile(
                r"((?:api_?key|token|secret|auth)\s*=\s*['\"]?)([^'\"\s]+)(['\"]?)", re.IGNORECASE
            ),
            r"\1***\3",
        ),
        # Authorization headers
        (re.compile(r"(Authorization:\s*(?:Bearer|Basic)\s+)([^\s]+)", re.IGNORECASE), r"\1***"),
        # Generic password field in JSON/dict
        (re.compile(r"(['\"]password['\"]:\s*['\"])([^'\"]+)(['\"])", re.IGNORECASE), r"\1***\3"),
    ]

    # Sensitive keys that should always be redacted
    SENSITIVE_KEYS = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "auth",
        "authorization",
        "private_key",
        "access_token",
        "refresh_token",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive information from log record.

        Args:
            record: Log record to filter

        Returns:
            True (always allow the record, just modify it)
        """
        # Redact the main message
        if isinstance(record.msg, str):
            record.msg = self._redact_string(record.msg)

        # Redact arguments if present
        if record.args:
            if isinstance(record.args, dict):
                record.args = self._redact_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._redact_string(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        return True

    def _redact_string(self, text: str) -> str:
        """Apply all redaction patterns to a string.

        Args:
            text: String to redact

        Returns:
            Redacted string
        """
        for pattern, replacement in self.PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    def _redact_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive values in a dictionary.

        Args:
            data: Dictionary to redact

        Returns:
            Dictionary with sensitive values redacted
        """
        redacted: dict[str, Any] = {}
        for key, value in data.items():
            # Check if key is sensitive
            if any(sensitive in str(key).lower() for sensitive in self.SENSITIVE_KEYS):
                redacted[key] = "***"
            elif isinstance(value, str):
                redacted[key] = self._redact_string(value)
            elif isinstance(value, dict):
                redacted[key] = self._redact_dict(value)
            else:
                redacted[key] = value
        return redacted


def setup_logging_with_redaction(
    level: str = "INFO",
    log_file: str | None = None,
    *,
    force: bool = False,
) -> None:
    """Set up logging with automatic secret redaction.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        force: Whether to replace existing root logger handlers
    """
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RedactFilter())

    handlers: list[logging.Handler] = [console_handler]

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RedactFilter())
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        force=force,
    )
