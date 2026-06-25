"""Secret redaction for logs: exact-value scrubbing plus a pattern fallback.

This tool's primary input is a credential-bearing connection string, so its own
secrets are *enumerable*: once a connection password is registered, every log
line can be scrubbed by exact match — deterministic and strictly stronger than
regex for the secrets we actually hold. Heuristic patterns remain as a fallback
for secrets we were never handed.

Usage:
    register_connection_string(url)   # extract + register the DSN password
    register_secret(value)            # register any known secret
    configure(settings)               # apply dotfile settings (enable, extras)

The module keeps a single process-wide :class:`Redactor`; :class:`RedactFilter`
(a logging filter) delegates to it.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import unquote

from sqlalchemy.engine.url import make_url

# Don't register very short values (too collision-prone), and never register
# common tokens that are substrings of harmless text (e.g. "postgres" would
# mangle "postgresql://...").
_MIN_SECRET_LENGTH = 4
_COMMON_VALUES = {
    "postgres",
    "postgresql",
    "mysql",
    "root",
    "admin",
    "user",
    "guest",
    "localhost",
    "password",
    "secret",
    "true",
    "false",
    "none",
    "null",
}
_PLACEHOLDER = "***"

_DEFAULT_LABELED_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # These are intentionally narrow, labeled fallback patterns. They are not a
    # generic secret detector; exact-value registration is the primary redaction
    # mechanism for secrets the application actually receives.
    # Connection strings: user:<password>@host -> user:***@host
    (re.compile(r"://([^:]+):([^@\s]+)@"), r"://\1:***@"),
    # password=value (optionally quoted)
    (re.compile(r"(password\s*=\s*['\"]?)([^'\"\s]+)(['\"]?)", re.IGNORECASE), r"\1***\3"),
    # api_key / token / secret / auth = value
    (
        re.compile(
            r"((?:api_?key|token|secret|auth)\s*=\s*['\"]?)([^'\"\s]+)(['\"]?)", re.IGNORECASE
        ),
        r"\1***\3",
    ),
    # Authorization: Bearer/Basic <token>
    (re.compile(r"(Authorization:\s*(?:Bearer|Basic)\s+)([^\s]+)", re.IGNORECASE), r"\1***"),
    # "password": "value" in JSON/dict text
    (re.compile(r"(['\"]password['\"]:\s*['\"])([^'\"]+)(['\"])", re.IGNORECASE), r"\1***\3"),
]
_DEFAULT_SENSITIVE_KEYS = {
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
_CONN_PASSWORD_RE = re.compile(r"://[^:/@\s]+:([^@\s/]+)@")


@dataclass
class RedactionSettings:
    """Redaction options sourced from the dotfile config."""

    enabled: bool = True
    extra_keys: list[str] = field(default_factory=list)
    extra_patterns: list[str] = field(default_factory=list)


class Redactor:
    """Holds registered secrets, patterns, and sensitive keys, and scrubs text."""

    def __init__(self) -> None:
        self.enabled = True
        self._exact: set[str] = set()
        self._patterns: list[tuple[re.Pattern[str], str]] = list(
            _DEFAULT_LABELED_SECRET_PATTERNS
        )
        self._keys: set[str] = set(_DEFAULT_SENSITIVE_KEYS)

    def reset(self) -> None:
        """Restore defaults and forget registered secrets (used by tests/startup)."""
        self.enabled = True
        self._exact.clear()
        self._patterns = list(_DEFAULT_LABELED_SECRET_PATTERNS)
        self._keys = set(_DEFAULT_SENSITIVE_KEYS)

    def register_secret(self, secret: str | None) -> None:
        """Register a known secret for exact-value scrubbing (with guards)."""
        if not secret:
            return
        value = str(secret)
        if len(value) < _MIN_SECRET_LENGTH or value.lower() in _COMMON_VALUES:
            return
        self._exact.add(value)

    def register_connection_string(self, url: str | None) -> None:
        """Extract and register the password from a connection URL."""
        if not url:
            return
        match = _CONN_PASSWORD_RE.search(url)
        if match:
            raw_password = match.group(1)
            self.register_secret(raw_password)
            self.register_secret(unquote(raw_password))
        try:
            self.register_secret(make_url(url).password)
        except Exception:
            return

    def add_sensitive_keys(self, keys: list[str]) -> None:
        self._keys.update(key.lower() for key in keys)

    def add_patterns(self, patterns: list[str]) -> None:
        for raw in patterns:
            try:
                self._patterns.append((re.compile(raw), _PLACEHOLDER))
            except re.error:
                logging.getLogger(__name__).warning(
                    "Ignoring invalid redaction pattern: %r", raw
                )

    def redact(self, text: str) -> str:
        """Scrub registered secrets (exact, longest-first) then apply patterns."""
        if not self.enabled:
            return text
        for secret in sorted(self._exact, key=len, reverse=True):
            text = text.replace(secret, _PLACEHOLDER)
        for pattern, replacement in self._patterns:
            text = pattern.sub(replacement, text)
        return text

    def redact_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Mask sensitive keys; recurse into nested dicts; scrub string values."""
        if not self.enabled:
            return data
        result: dict[str, Any] = {}
        for key, value in data.items():
            if any(sensitive in str(key).lower() for sensitive in self._keys):
                result[key] = _PLACEHOLDER
            elif isinstance(value, str):
                result[key] = self.redact(value)
            elif isinstance(value, dict):
                result[key] = self.redact_dict(value)
            else:
                result[key] = value
        return result


_redactor = Redactor()


def register_secret(secret: str | None) -> None:
    """Register a known secret with the process-wide redactor."""
    _redactor.register_secret(secret)


def register_connection_string(url: str | None) -> None:
    """Register a connection URL's password with the process-wide redactor."""
    _redactor.register_connection_string(url)


def configure(settings: RedactionSettings) -> None:
    """Apply dotfile redaction settings to the process-wide redactor."""
    _redactor.enabled = settings.enabled
    _redactor.add_sensitive_keys(settings.extra_keys)
    _redactor.add_patterns(settings.extra_patterns)
    if not settings.enabled:
        logging.getLogger(__name__).warning(
            "Secret redaction is DISABLED via config; secrets may appear in logs and log files."
        )


def reset() -> None:
    """Reset the process-wide redactor to defaults."""
    _redactor.reset()


def _parse_bool(value: Any, *, default: bool) -> bool:
    """Parse config booleans that may arrive as strings after interpolation."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def settings_from_mapping(data: dict[str, Any]) -> RedactionSettings:
    """Build :class:`RedactionSettings` from a parsed config mapping's ``redaction`` section."""
    section = data.get("redaction") if isinstance(data, dict) else None
    if not isinstance(section, dict):
        return RedactionSettings()
    return RedactionSettings(
        enabled=_parse_bool(section.get("enabled"), default=True),
        extra_keys=[str(key) for key in section.get("extra_keys") or []],
        extra_patterns=[str(pattern) for pattern in section.get("extra_patterns") or []],
    )


class RedactFilter(logging.Filter):
    """Logging filter that scrubs secrets from every record via the redactor."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            # Redact argument values, then assemble and redact the final
            # message. Formatting first means pattern redaction can never mangle
            # a %-placeholder in the template (e.g. one matching "://user:%s@").
            if isinstance(record.args, dict):
                record.args = _redactor.redact_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    _redactor.redact(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
            try:
                record.msg = _redactor.redact(record.getMessage())
                record.args = ()
            except (TypeError, ValueError):
                # Malformed log call (args don't match the template); redact the
                # template best-effort and let logging surface the format error.
                if isinstance(record.msg, str):
                    record.msg = _redactor.redact(record.msg)
        elif isinstance(record.msg, str):
            record.msg = _redactor.redact(record.msg)
        return True
