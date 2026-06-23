"""Tests for credential helpers."""

from __future__ import annotations

from hypothesis.config.credentials import CredentialManager


def test_sanitize_connection_string_hides_password() -> None:
    credential = "fixture_credential"
    url = "postgresql://user" + ":" + credential + "@example.test:5432/db"
    sanitized = CredentialManager.sanitize_connection_string(url)

    assert credential not in sanitized
    assert sanitized == "postgresql://user:" + "***" + "@example.test:5432/db"
