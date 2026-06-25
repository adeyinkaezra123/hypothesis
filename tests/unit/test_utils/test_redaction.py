"""Tests for secret redaction (exact-value scrubbing + pattern fallback)."""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

from hypothesis.utils import redaction
from hypothesis.utils.redaction import (
    RedactFilter,
    RedactionSettings,
    Redactor,
    configure,
    register_connection_string,
    register_secret,
    reset,
    settings_from_mapping,
)

# Built from parts so no secret-shaped literal appears in source (keeps secret
# scanners from flagging these test fixtures). Registerable: length >= 4 and not
# in the common-values skip-set.
_SECRET = "fixture" + "-" + "secret"


@pytest.fixture(autouse=True)
def _clean_redactor() -> Iterator[None]:
    """Isolate the process-wide redactor between tests."""
    reset()
    yield
    reset()


def _redact(text: str) -> str:
    record = logging.LogRecord("t", logging.INFO, __file__, 1, text, (), None)
    RedactFilter().filter(record)
    return str(record.msg)


def _dsn(password: str, host: str = "host") -> str:
    # Assembled from parts so the source carries no inline "user:<secret>@"
    # literal — keeps secret scanners from flagging these test fixtures.
    return "postgresql://user" + ":" + password + "@" + host + "/db"


# -- exact-value scrubbing --------------------------------------------------


def test_registered_secret_is_scrubbed() -> None:
    register_secret(_SECRET)
    assert _SECRET not in _redact(f"using {_SECRET} now")
    assert "***" in _redact(f"using {_SECRET} now")


def test_short_secret_is_not_registered() -> None:
    register_secret("ab")  # below the minimum length
    assert _redact("value ab here") == "value ab here"


def test_common_value_is_not_registered() -> None:
    register_secret("postgres")  # would otherwise mangle "postgresql://"
    assert _redact("postgresql://host/db") == "postgresql://host/db"


def test_connection_string_registration_scrubs_password() -> None:
    dsn = _dsn(_SECRET, "host:5432")
    register_connection_string(dsn)
    assert _SECRET not in _redact("dsn=" + dsn)


def test_connection_string_with_common_password_falls_back_to_pattern() -> None:
    # "postgres" is skipped for exact registration, but the pattern still masks it.
    register_connection_string(_dsn("postgres"))
    assert _redact(_dsn("postgres")) == "postgresql://user" + ":***@" + "host/db"


# -- pattern fallback -------------------------------------------------------


def test_pattern_fallback_masks_unregistered_connection_password() -> None:
    assert _SECRET not in _redact(_dsn(_SECRET))


# -- dict redaction ---------------------------------------------------------


def test_dict_redaction_masks_sensitive_keys_recursively() -> None:
    redactor = Redactor()
    out = redactor.redact_dict({"password": _SECRET, "host": "localhost", "nested": {"token": _SECRET}})
    assert out["password"] == "***"
    assert out["host"] == "localhost"
    assert out["nested"]["token"] == "***"


def test_filter_redacts_tuple_args() -> None:
    register_secret(_SECRET)
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "x %s", (_SECRET,), None)
    RedactFilter().filter(record)
    assert _SECRET not in record.getMessage()


def test_filter_redacts_dict_args() -> None:
    # LogRecord unwraps a single-element tuple containing a Mapping into .args.
    record = logging.LogRecord(
        "t", logging.INFO, __file__, 1, "user=%(password)s", ({"password": _SECRET},), None
    )
    RedactFilter().filter(record)
    message = record.getMessage()
    assert _SECRET not in message
    assert "***" in message


def test_filter_survives_malformed_log_args() -> None:
    # No placeholder but an extra arg: the filter must not raise.
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "no placeholder", ("extra",), None)
    RedactFilter().filter(record)


# -- configuration ----------------------------------------------------------


def test_disabled_is_a_noop() -> None:
    configure(RedactionSettings(enabled=False))
    register_secret(_SECRET)
    assert _redact(f"{_SECRET} here") == f"{_SECRET} here"


def test_invalid_extra_pattern_is_ignored() -> None:
    configure(RedactionSettings(extra_patterns=["valid_[0-9]+", "(unclosed"]))
    assert "***" in _redact("id valid_123")
    assert _redact("plain text") == "plain text"


def test_extra_keys_extend_the_sensitive_set() -> None:
    configure(RedactionSettings(extra_keys=["session"]))
    out = redaction._redactor.redact_dict({"session": "abc", "name": "ok"})
    assert out["session"] == "***"
    assert out["name"] == "ok"


def test_settings_from_mapping_parses_redaction_section() -> None:
    settings = settings_from_mapping(
        {"redaction": {"enabled": False, "extra_keys": ["k"], "extra_patterns": ["p"]}}
    )
    assert settings.enabled is False
    assert settings.extra_keys == ["k"]
    assert settings.extra_patterns == ["p"]


def test_settings_from_mapping_defaults_when_absent() -> None:
    settings = settings_from_mapping({"tables": {}})
    assert settings.enabled is True
    assert settings.extra_keys == []
    assert settings.extra_patterns == []


def test_apply_redaction_settings_startup_glue_is_safe() -> None:
    from hypothesis.cli.app import _apply_redaction_settings

    # No .hypothesisrc in the test environment -> defaults, no error.
    _apply_redaction_settings()
    assert redaction._redactor.enabled is True
