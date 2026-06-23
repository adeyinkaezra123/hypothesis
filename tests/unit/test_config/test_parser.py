"""Tests for configuration file parser."""

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from hypothesis.config.parser import ConfigParser


class TestConfigParserInit:
    """Test ConfigParser initialization."""

    def test_init_with_explicit_path(self, tmp_path: Path) -> None:
        """Test initialization with explicit config path."""

        config_file = tmp_path / ".hypothesisrc"
        config_file.write_text("development:\n  host: localhost\n")

        parser = ConfigParser(config_path=config_file)

        assert parser.config_path == config_file
        assert parser.config is not None

    def test_init_without_path_finds_config(self, config_dir: Path) -> None:
        """Test initialization without path searches default locations."""
        config_file = config_dir / ".hypothesisrc"
        config_file.write_text("test:\n  host: localhost\n")

        parser = ConfigParser()

        assert parser.config_path == config_file
        assert parser.config is not None

    def test_init_without_config_file(self, config_dir: Path) -> None:
        """Test initialization when no config file exists."""
        parser = ConfigParser()

        assert parser.config_path is None
        assert parser.config == {}


class TestFindConfig:
    """Test _find_config method."""

    @pytest.mark.parametrize(
        "filename",
        [".hypothesisrc", ".hypothesis.yml"],
    )
    def test_finds_config_files(self, config_dir: Path, filename: str) -> None:
        """Test finding various config file names."""
        config_file = config_dir / filename
        config_file.write_text("test: config")

        parser = ConfigParser()

        assert parser.config_path == config_file

    def test_priority_order(self, config_dir: Path) -> None:
        """Test that .hypothesisrc has priority over .hypothesis.yml."""
        rc_file = config_dir / ".hypothesisrc"
        yml_file = config_dir / ".hypothesis.yml"
        rc_file.write_text("from: rc")
        yml_file.write_text("from: yml")

        parser = ConfigParser()

        assert parser.config_path == rc_file

    def test_home_paths_in_default_paths(self) -> None:
        """Test that home directory paths are included in DEFAULT_PATHS."""
        from hypothesis.config.parser import ConfigParser

        # Verify home paths are in the search list
        home_paths = [p for p in ConfigParser.DEFAULT_PATHS if str(p).startswith(str(Path.home()))]
        assert len(home_paths) == 2  # Should have ~/.hypothesisrc and ~/.hypothesis.yml

    def test_returns_none_when_no_config_found(self, config_dir: Path) -> None:
        """Test returns None when no config file exists."""
        parser = ConfigParser()

        assert parser.config_path is None


class TestLoadConfig:
    """Test _load_config method."""

    def test_loads_valid_yaml(
        self, tmp_path: Path, sample_config: dict[str, dict[str, Any]]
    ) -> None:
        """Test loading valid YAML config."""
        config_file = tmp_path / ".hypothesisrc"
        config_file.write_text(yaml.dump(sample_config))

        parser = ConfigParser(config_path=config_file)

        assert parser.config == sample_config

    @pytest.mark.parametrize(
        "content,expected",
        [
            ("", {}),  # Empty file
            ("   \n\n   ", {}),  # Whitespace only
            ("# Just comments\n# More comments", {}),  # Comments only
        ],
    )
    def test_handles_empty_files(
        self, tmp_path: Path, content: str, expected: dict[str, Any]
    ) -> None:
        """Test handling of empty or whitespace-only files."""
        config_file = tmp_path / ".hypothesisrc"
        config_file.write_text(content)

        parser = ConfigParser(config_path=config_file)

        assert parser.config == expected

    def test_handles_invalid_yaml(self, tmp_path: Path) -> None:
        """Test handling of invalid YAML syntax."""
        config_file = tmp_path / ".hypothesisrc"
        config_file.write_text("invalid: yaml: syntax: here:")

        parser = ConfigParser(config_path=config_file)

        assert parser.config == {}

    def test_handles_missing_file(self, tmp_path: Path) -> None:
        """Test handling of missing config file."""
        config_file = tmp_path / "nonexistent.yml"

        parser = ConfigParser(config_path=config_file)

        assert parser.config == {}

    @pytest.mark.skipif(os.name == "nt", reason="Permission tests unreliable on Windows")
    def test_handles_permission_error(self, tmp_path: Path) -> None:
        """Test handling of permission denied."""
        config_file = tmp_path / ".hypothesisrc"
        config_file.write_text("test: config")
        config_file.chmod(0o000)

        try:
            parser = ConfigParser(config_path=config_file)
            assert parser.config == {}
        finally:
            config_file.chmod(0o644)


class TestInterpolateEnvironment:
    """Test _interpolate_environment method."""

    def test_simple_variable_substitution(self, clean_env: Callable[[str, str], None]) -> None:
        """Test simple ${VAR} substitution."""
        clean_env("TEST_VAR", "test_value")

        parser = ConfigParser()
        config = {"key": "${TEST_VAR}"}
        result = parser._interpolate_environment(config)

        assert result == {"key": "test_value"}

    def test_variable_with_default(self) -> None:
        """Test ${VAR:-default} substitution."""
        os.environ.pop("NONEXISTENT_VAR", None)

        parser = ConfigParser()
        config = {"key": "${NONEXISTENT_VAR:-default_value}"}
        result = parser._interpolate_environment(config)

        assert result == {"key": "default_value"}

    def test_variable_with_default_when_var_exists(
        self, clean_env: Callable[[str, str], None]
    ) -> None:
        """Test ${VAR:-default} uses variable when it exists."""
        clean_env("EXISTING_VAR", "actual_value")

        parser = ConfigParser()
        config = {"key": "${EXISTING_VAR:-default_value}"}
        result = parser._interpolate_environment(config)

        assert result == {"key": "actual_value"}

    def test_multiple_variables_in_string(self, clean_env: Callable[[str, str], None]) -> None:
        """Test multiple variables in same string."""
        clean_env("HOST", "localhost")
        clean_env("PORT", "5432")

        parser = ConfigParser()
        config = {"connection": "${HOST}:${PORT}"}
        result = parser._interpolate_environment(config)

        assert result == {"connection": "localhost:5432"}

    def test_nested_dict_interpolation(self, clean_env: Callable[[str, str], None]) -> None:
        """Test interpolation in nested dictionaries."""
        clean_env("DB_HOST", "db.example.com")
        clean_env("DB_PORT", "3306")

        parser = ConfigParser()
        config = {
            "database": {
                "primary": {"host": "${DB_HOST}", "port": "${DB_PORT}"},
                "replica": {"host": "${DB_HOST}", "port": "3307"},
            }
        }
        result = parser._interpolate_environment(config)

        assert result == {
            "database": {
                "primary": {"host": "db.example.com", "port": "3306"},
                "replica": {"host": "db.example.com", "port": "3307"},
            }
        }

    def test_list_interpolation(self, clean_env: Callable[[str, str], None]) -> None:
        """Test interpolation in lists."""
        clean_env("SERVER1", "server1.example.com")
        clean_env("SERVER2", "server2.example.com")

        parser = ConfigParser()
        config = {"servers": ["${SERVER1}", "${SERVER2}", "server3.example.com"]}
        result = parser._interpolate_environment(config)

        assert result == {
            "servers": [
                "server1.example.com",
                "server2.example.com",
                "server3.example.com",
            ]
        }

    @pytest.mark.parametrize(
        "value",
        [42, 3.14, True, False, None],
    )
    def test_non_string_values_unchanged(self, value: object) -> None:
        """Test that non-string values are not modified."""
        parser = ConfigParser()
        config = {"key": value}
        result = parser._interpolate_environment(config)

        assert result == config

    def test_whitespace_in_variable_name(self, clean_env: Callable[[str, str], None]) -> None:
        """Test handling of whitespace in variable names."""
        clean_env("VAR_WITH_SPACE", "value")

        parser = ConfigParser()
        config = {"key": "${ VAR_WITH_SPACE }"}
        result = parser._interpolate_environment(config)

        assert result == {"key": "value"}


class TestParse:
    """Test parse method."""

    def test_parse_returns_interpolated_config(self, clean_env: Callable[[str, str], None]) -> None:
        """Test that parse returns interpolated configuration."""
        clean_env("TEST_HOST", "localhost")

        parser = ConfigParser()
        config_content = {"database": {"host": "${TEST_HOST}"}}
        result = parser.parse(config_content)

        assert result == {"database": {"host": "localhost"}}
        assert parser.config == result


class TestIntegration:
    """Integration tests for ConfigParser."""

    def test_full_config_workflow(
        self,
        config_dir: Path,
        clean_env: Callable[[str, str], None],
        integration_config_content: str,
    ) -> None:
        """Test complete workflow from file to parsed config."""
        clean_env("DB_HOST", "prod.example.com")
        clean_env("DB_PORT", "5432")

        config_file = config_dir / ".hypothesisrc"
        config_file.write_text(integration_config_content)

        parser = ConfigParser()

        assert parser.config["production"]["host"] == "prod.example.com"
        assert parser.config["production"]["port"] == "5432"
        assert parser.config["development"]["host"] == "localhost"
        assert parser.config["development"]["port"] == "5432"
