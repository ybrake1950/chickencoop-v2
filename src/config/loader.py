"""
Configuration file loading utilities.

This module handles loading JSON configuration files with support for
merging base and device-specific configurations.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict


def load_config(path: Path) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    Args:
        path: Path to the configuration file

    Returns:
        Dictionary containing configuration data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    content = path.read_text()
    if not content.strip():
        raise json.JSONDecodeError("Empty file", content, 0)

    return json.loads(content)


def load_aws_config(path: Path) -> Dict[str, Any]:
    """
    Load AWS configuration from a JSON file.

    Args:
        path: Path to the AWS configuration file

    Returns:
        Dictionary containing AWS configuration data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    return load_config(path)


def load_device_config(path: Path) -> Dict[str, Any]:
    """
    Load device-specific configuration from a JSON file.

    Args:
        path: Path to the device configuration file

    Returns:
        Dictionary containing device configuration data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    return load_config(path)


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two configuration dictionaries.

    Override values take precedence. Nested dictionaries are merged recursively.

    Args:
        base: Base configuration dictionary
        override: Override configuration dictionary

    Returns:
        Merged configuration dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def get_config_path(filename: str) -> Path:
    """
    Get the path to a configuration file.

    Uses CONFIG_DIR environment variable if set, otherwise defaults
    to 'config' directory relative to project root.

    Args:
        filename: Name of the configuration file

    Returns:
        Path to the configuration file
    """
    config_dir = os.environ.get("CONFIG_DIR")
    if config_dir:
        return Path(config_dir) / filename

    # Default to config directory relative to project root
    return Path(__file__).parent.parent.parent / "config" / filename


def get_device_config_path() -> Path:
    """
    Get the path to the device-specific configuration file.

    Uses COOP_ID environment variable to determine which device config to load.

    Returns:
        Path to the device configuration file
    """
    coop_id = os.environ.get("COOP_ID", "default")
    return get_config_path(f"devices/{coop_id}.json")


class ConfigLoader:
    """Configuration loader that caches loaded configuration."""

    def __init__(self):
        self._config: Dict[str, Any] = {}

    def load(self, path: Path) -> Dict[str, Any]:
        """Load configuration from a file."""
        self._config = load_config(path)
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    @property
    def data(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self._config


_config_instance = None


def get_config() -> ConfigLoader:
    """Get or create a singleton ConfigLoader instance."""
    global _config_instance  # pylint: disable=global-statement
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance
