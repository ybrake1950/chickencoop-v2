"""
TDD Tests: Configuration Loading

These tests define the expected behavior for loading configuration files.
Implement src/config/loader.py to make these tests pass.

Run: pytest tdd/phase1_foundation/config/test_config_loader.py -v
"""

import json
import pytest
from pathlib import Path
from typing import Any, Dict


# =============================================================================
# Test: Basic Configuration Loading
# =============================================================================

class TestConfigLoader:
    """Tests for configuration file loading functionality."""

    def test_load_config_returns_dict(self, config_file: Path):
        """Loading a valid config file should return a dictionary."""
        from src.config.loader import load_config

        result = load_config(config_file)

        assert isinstance(result, dict)

    def test_load_config_contains_expected_keys(self, config_file: Path):
        """Loaded config should contain all required top-level keys."""
        from src.config.loader import load_config

        result = load_config(config_file)

        assert "sensors" in result
        assert "camera" in result
        assert "motion" in result

    def test_load_config_with_nonexistent_file_raises_error(self, tmp_path: Path):
        """Loading a non-existent file should raise FileNotFoundError."""
        from src.config.loader import load_config

        nonexistent = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            load_config(nonexistent)

    def test_load_config_with_invalid_json_raises_error(self, tmp_path: Path):
        """Loading invalid JSON should raise a JSONDecodeError."""
        from src.config.loader import load_config

        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_config(invalid_file)

    def test_load_config_with_empty_file_raises_error(self, tmp_path: Path):
        """Loading an empty file should raise an appropriate error."""
        from src.config.loader import load_config

        empty_file = tmp_path / "empty.json"
        empty_file.write_text("")

        with pytest.raises((json.JSONDecodeError, ValueError)):
            load_config(empty_file)

    def test_load_config_preserves_nested_structure(self, config_file: Path):
        """Nested configuration structures should be preserved."""
        from src.config.loader import load_config

        result = load_config(config_file)

        assert result["sensors"]["temperature"]["unit"] == "fahrenheit"
        assert result["camera"]["resolution"] == [1280, 720]


# =============================================================================
# Test: AWS Configuration Loading
# =============================================================================

class TestAWSConfigLoader:
    """Tests for AWS configuration loading."""

    def test_load_aws_config_returns_dict(self, aws_config_file: Path):
        """Loading AWS config should return a dictionary."""
        from src.config.loader import load_aws_config

        result = load_aws_config(aws_config_file)

        assert isinstance(result, dict)

    def test_load_aws_config_contains_required_services(self, aws_config_file: Path):
        """AWS config should contain S3, IoT, and SNS configurations."""
        from src.config.loader import load_aws_config

        result = load_aws_config(aws_config_file)

        assert "s3" in result
        assert "iot" in result
        assert "sns" in result

    def test_load_aws_config_has_region(self, aws_config_file: Path):
        """AWS config should specify a region."""
        from src.config.loader import load_aws_config

        result = load_aws_config(aws_config_file)

        assert "region" in result
        assert isinstance(result["region"], str)


# =============================================================================
# Test: Device-Specific Configuration
# =============================================================================

class TestDeviceConfigLoader:
    """Tests for device-specific configuration loading."""

    def test_load_device_config_returns_dict(self, tmp_path: Path, sample_device_config: Dict):
        """Loading device config should return a dictionary."""
        from src.config.loader import load_device_config

        device_file = tmp_path / "device.json"
        device_file.write_text(json.dumps(sample_device_config))

        result = load_device_config(device_file)

        assert isinstance(result, dict)

    def test_load_device_config_has_device_id(self, tmp_path: Path, sample_device_config: Dict):
        """Device config should contain device_id."""
        from src.config.loader import load_device_config

        device_file = tmp_path / "device.json"
        device_file.write_text(json.dumps(sample_device_config))

        result = load_device_config(device_file)

        assert "device_id" in result


# =============================================================================
# Test: Configuration Merging
# =============================================================================

class TestConfigMerger:
    """Tests for merging base and device-specific configurations."""

    def test_merge_configs_combines_dicts(self):
        """Merging configs should combine dictionaries."""
        from src.config.loader import merge_configs

        base = {"a": 1, "b": 2}
        override = {"c": 3}

        result = merge_configs(base, override)

        assert result == {"a": 1, "b": 2, "c": 3}

    def test_merge_configs_override_takes_precedence(self):
        """Override values should take precedence over base values."""
        from src.config.loader import merge_configs

        base = {"resolution": [1280, 720]}
        override = {"resolution": [1920, 1080]}

        result = merge_configs(base, override)

        assert result["resolution"] == [1920, 1080]

    def test_merge_configs_deep_merge_nested_dicts(self):
        """Nested dictionaries should be merged recursively."""
        from src.config.loader import merge_configs

        base = {"camera": {"resolution": [1280, 720], "framerate": 24}}
        override = {"camera": {"framerate": 30}}

        result = merge_configs(base, override)

        assert result["camera"]["resolution"] == [1280, 720]
        assert result["camera"]["framerate"] == 30

    def test_merge_configs_preserves_base_when_no_override(self):
        """Base values should be preserved when not overridden."""
        from src.config.loader import merge_configs

        base = {"sensors": {"enabled": True}}
        override = {}

        result = merge_configs(base, override)

        assert result["sensors"]["enabled"] is True


# =============================================================================
# Test: Configuration Path Resolution
# =============================================================================

class TestConfigPathResolver:
    """Tests for resolving configuration file paths."""

    def test_get_config_path_returns_path_object(self):
        """get_config_path should return a Path object."""
        from src.config.loader import get_config_path

        result = get_config_path("config.json")

        assert isinstance(result, Path)

    def test_get_config_path_with_config_dir_env(self, tmp_path: Path, monkeypatch):
        """Should use CONFIG_DIR environment variable if set."""
        from src.config.loader import get_config_path

        monkeypatch.setenv("CONFIG_DIR", str(tmp_path))

        result = get_config_path("config.json")

        assert result.parent == tmp_path

    def test_get_device_config_path_uses_coop_id(self, monkeypatch):
        """Device config path should use COOP_ID environment variable."""
        from src.config.loader import get_device_config_path

        monkeypatch.setenv("COOP_ID", "coop1")

        result = get_device_config_path()

        assert "coop1" in str(result)
