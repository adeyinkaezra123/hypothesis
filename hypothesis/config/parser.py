"""
Parses Hypothesis config files with support for environment variables and interpolation.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, cast

import yaml

logger = logging.getLogger(__name__)


class ConfigParser:
    HOME_PATH = Path.home()
    DEFAULT_PATHS = [
        Path("./.hypothesisrc"),
        Path("./.hypothesis.yml"),
        HOME_PATH / ".hypothesisrc",
        HOME_PATH / ".hypothesis.yml",
    ]

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or self._find_config()
        self.config = self._load_config()

        """
        Initialize config parser.

        Args:
            config_path: Optional path to config file. If None, searches default locations.
        """

    def parse(self, config_content: dict[str, Any]) -> dict[str, Any]:
        """
        Parse config file and return dictionary of key-value pairs.

        Returns:
            Dictionary of key-value pairs from config file.
        """

        interpolated_config = self._interpolate_environment(config_content)

        self.config = interpolated_config

        return self.config

    def _find_config(self) -> Path | None:
        """
        Find config file in default locations.

        Returns:
            Path to first config file found, or None if not found.
        """
        for path in self.DEFAULT_PATHS:
            if path.is_file():
                return path.resolve()
        return None

    def _load_config(self) -> dict[str, Any]:
        """
        Load config file and return dictionary of key-value pairs.

        Returns:
            dict: Parsed config, or empty dict if missing/unreadable.
        """
        if not self.config_path:
            logger.debug("No config file found")
            return {}

        try:
            with open(self.config_path) as f:
                config_content = yaml.safe_load(f)
                if not config_content:
                    logger.warning("Config file is empty")
                    return {}
                return self.parse(config_content)

        except (PermissionError, FileNotFoundError) as e:
            logger.error(f"Config file not accessible: {e}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML syntax: {e}")
            return {}

    def _interpolate_environment(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Interpolate environment variables in config values.

        Supports:
        - ${VAR} - simple variable substitution
        - ${VAR:-default} - variable with default value

        Args:
            config: Dictionary of config values.

        Returns:
            Dictionary with interpolated values.
        """

        def interpolate_value(value: Any) -> Any:
            """Recursively interpolate environment variables in any value type."""
            if isinstance(value, str):
                # Pattern matches ${VAR} or ${VAR:-default}
                pattern = r"\$\{([^}:]+)(?::-([^}]*))?\}"

                def replace_var(match: re.Match[str]) -> str:
                    var_name = match.group(1).strip()
                    default_value = match.group(2) if match.group(2) is not None else ""

                    # Get environment variable, use default if not found
                    return os.getenv(var_name, default_value)

                return re.sub(pattern, replace_var, value)

            elif isinstance(value, dict):
                return {k: interpolate_value(v) for k, v in value.items()}

            elif isinstance(value, list):
                return [interpolate_value(item) for item in value]

            else:
                return value

        return cast("dict[str, Any]", interpolate_value(config))


class HypothesisConfigError(Exception):
    """Exception raised when config file is missing."""
