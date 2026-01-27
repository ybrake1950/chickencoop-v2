"""
TDD Tests: Configuration Validation

These tests define the expected behavior for validating configuration schemas.
Implement src/config/validation.py to make these tests pass.

Run: pytest tdd/phase1_foundation/config/test_config_validation.py -v
"""

import pytest
from typing import Any, Dict


# =============================================================================
# Test: Schema Validation
# =============================================================================

class TestConfigValidation:
    """Tests for configuration schema validation."""

    def test_validate_config_accepts_valid_config(self, sample_config: Dict[str, Any]):
        """Valid configuration should pass validation."""
        from src.config.validation import validate_config

        # Should not raise
        result = validate_config(sample_config)

        assert result is True

    def test_validate_config_rejects_empty_dict(self):
        """Empty configuration should fail validation."""
        from src.config.validation import validate_config, ConfigValidationError

        with pytest.raises(ConfigValidationError):
            validate_config({})

    def test_validate_config_requires_sensors_section(self, sample_config: Dict[str, Any]):
        """Configuration must have sensors section."""
        from src.config.validation import validate_config, ConfigValidationError

        del sample_config["sensors"]

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(sample_config)

        assert "sensors" in str(exc_info.value).lower()

    def test_validate_config_requires_camera_section(self, sample_config: Dict[str, Any]):
        """Configuration must have camera section."""
        from src.config.validation import validate_config, ConfigValidationError

        del sample_config["camera"]

        with pytest.raises(ConfigValidationError) as exc_info:
            validate_config(sample_config)

        assert "camera" in str(exc_info.value).lower()


# =============================================================================
# Test: Sensor Configuration Validation
# =============================================================================

class TestSensorConfigValidation:
    """Tests for sensor configuration validation."""

    def test_validate_sensor_config_accepts_valid_config(self, sample_config: Dict[str, Any]):
        """Valid sensor config should pass validation."""
        from src.config.validation import validate_sensor_config

        result = validate_sensor_config(sample_config["sensors"])

        assert result is True

    def test_validate_sensor_read_interval_is_positive(self, sample_config: Dict[str, Any]):
        """Sensor read interval must be a positive integer."""
        from src.config.validation import validate_sensor_config, ConfigValidationError

        sample_config["sensors"]["read_interval"] = -1

        with pytest.raises(ConfigValidationError):
            validate_sensor_config(sample_config["sensors"])

    def test_validate_temperature_thresholds_are_valid(self, sample_config: Dict[str, Any]):
        """Temperature thresholds must be valid (min < max)."""
        from src.config.validation import validate_sensor_config, ConfigValidationError

        sample_config["sensors"]["temperature"]["min_threshold"] = 100
        sample_config["sensors"]["temperature"]["max_threshold"] = 50

        with pytest.raises(ConfigValidationError):
            validate_sensor_config(sample_config["sensors"])

    def test_validate_humidity_thresholds_in_valid_range(self, sample_config: Dict[str, Any]):
        """Humidity thresholds must be between 0 and 100."""
        from src.config.validation import validate_sensor_config, ConfigValidationError

        sample_config["sensors"]["humidity"]["max_threshold"] = 150

        with pytest.raises(ConfigValidationError):
            validate_sensor_config(sample_config["sensors"])


# =============================================================================
# Test: Camera Configuration Validation
# =============================================================================

class TestCameraConfigValidation:
    """Tests for camera configuration validation."""

    def test_validate_camera_config_accepts_valid_config(self, sample_config: Dict[str, Any]):
        """Valid camera config should pass validation."""
        from src.config.validation import validate_camera_config

        result = validate_camera_config(sample_config["camera"])

        assert result is True

    def test_validate_resolution_is_list_of_two_integers(self, sample_config: Dict[str, Any]):
        """Resolution must be [width, height] list."""
        from src.config.validation import validate_camera_config, ConfigValidationError

        sample_config["camera"]["resolution"] = [1280]  # Missing height

        with pytest.raises(ConfigValidationError):
            validate_camera_config(sample_config["camera"])

    def test_validate_resolution_values_are_positive(self, sample_config: Dict[str, Any]):
        """Resolution values must be positive integers."""
        from src.config.validation import validate_camera_config, ConfigValidationError

        sample_config["camera"]["resolution"] = [-1280, 720]

        with pytest.raises(ConfigValidationError):
            validate_camera_config(sample_config["camera"])

    def test_validate_framerate_in_valid_range(self, sample_config: Dict[str, Any]):
        """Framerate must be between 1 and 120."""
        from src.config.validation import validate_camera_config, ConfigValidationError

        sample_config["camera"]["framerate"] = 0

        with pytest.raises(ConfigValidationError):
            validate_camera_config(sample_config["camera"])

    def test_validate_rotation_in_valid_values(self, sample_config: Dict[str, Any]):
        """Rotation must be 0, 90, 180, or 270."""
        from src.config.validation import validate_camera_config, ConfigValidationError

        sample_config["camera"]["rotation"] = 45

        with pytest.raises(ConfigValidationError):
            validate_camera_config(sample_config["camera"])


# =============================================================================
# Test: Motion Configuration Validation
# =============================================================================

class TestMotionConfigValidation:
    """Tests for motion detection configuration validation."""

    def test_validate_motion_config_accepts_valid_config(self, sample_config: Dict[str, Any]):
        """Valid motion config should pass validation."""
        from src.config.validation import validate_motion_config

        result = validate_motion_config(sample_config["motion"])

        assert result is True

    def test_validate_sensitivity_in_range(self, sample_config: Dict[str, Any]):
        """Sensitivity must be between 0 and 100."""
        from src.config.validation import validate_motion_config, ConfigValidationError

        sample_config["motion"]["sensitivity"] = 150

        with pytest.raises(ConfigValidationError):
            validate_motion_config(sample_config["motion"])

    def test_validate_min_area_is_positive(self, sample_config: Dict[str, Any]):
        """Minimum detection area must be positive."""
        from src.config.validation import validate_motion_config, ConfigValidationError

        sample_config["motion"]["min_area"] = -100

        with pytest.raises(ConfigValidationError):
            validate_motion_config(sample_config["motion"])

    def test_validate_recording_duration_is_positive(self, sample_config: Dict[str, Any]):
        """Recording duration must be positive."""
        from src.config.validation import validate_motion_config, ConfigValidationError

        sample_config["motion"]["recording_duration"] = 0

        with pytest.raises(ConfigValidationError):
            validate_motion_config(sample_config["motion"])


# =============================================================================
# Test: AWS Configuration Validation
# =============================================================================

class TestAWSConfigValidation:
    """Tests for AWS configuration validation."""

    def test_validate_aws_config_accepts_valid_config(self, sample_aws_config: Dict[str, Any]):
        """Valid AWS config should pass validation."""
        from src.config.validation import validate_aws_config

        result = validate_aws_config(sample_aws_config)

        assert result is True

    def test_validate_aws_config_requires_region(self, sample_aws_config: Dict[str, Any]):
        """AWS config must specify a region."""
        from src.config.validation import validate_aws_config, ConfigValidationError

        del sample_aws_config["region"]

        with pytest.raises(ConfigValidationError):
            validate_aws_config(sample_aws_config)

    def test_validate_s3_bucket_name_format(self, sample_aws_config: Dict[str, Any]):
        """S3 bucket name must follow AWS naming rules."""
        from src.config.validation import validate_aws_config, ConfigValidationError

        sample_aws_config["s3"]["bucket"] = "Invalid_Bucket_Name!"

        with pytest.raises(ConfigValidationError):
            validate_aws_config(sample_aws_config)

    def test_validate_sns_topic_arn_format(self, sample_aws_config: Dict[str, Any]):
        """SNS topic ARN must be valid format."""
        from src.config.validation import validate_aws_config, ConfigValidationError

        sample_aws_config["sns"]["topic_arn"] = "invalid-arn"

        with pytest.raises(ConfigValidationError):
            validate_aws_config(sample_aws_config)

    def test_validate_iot_endpoint_format(self, sample_aws_config: Dict[str, Any]):
        """IoT endpoint must be valid hostname."""
        from src.config.validation import validate_aws_config, ConfigValidationError

        sample_aws_config["iot"]["endpoint"] = ""

        with pytest.raises(ConfigValidationError):
            validate_aws_config(sample_aws_config)
