"""Pytest fixtures for config tests."""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[str, str], None]]:
    """Clean environment fixture that removes test variables after use."""
    test_vars: list[str] = []

    def set_env(key: str, value: str) -> None:
        """Set environment variable and track for cleanup."""
        monkeypatch.setenv(key, value)
        test_vars.append(key)

    yield set_env


@pytest.fixture
def config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary config directory and change to it."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def sample_config() -> dict[str, dict[str, Any]]:
    """Return a sample configuration dictionary."""
    return {
        "development": {
            "dialect": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "myapp_dev",
        },
        "production": {
            "dialect": "postgresql",
            "host": "db.example.com",
            "port": 5432,
            "database": "myapp_prod",
        },
    }


@pytest.fixture
def integration_config_content() -> str:
    """Return sample config content with environment variables for integration tests."""
    from tests.fixtures.configs.sample_configs import SAMPLE_CONFIG_WITH_ENV_VARS

    return SAMPLE_CONFIG_WITH_ENV_VARS
