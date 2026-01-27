"""
IMPLEMENTATION STUB: src/config/validation.py

Copy this file to src/config/validation.py and complete the implementation.
Run: pytest tdd/phase1_foundation/config/test_config_validation.py -v
"""

from typing import Any, Dict


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message)


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate the main application configuration.

    Args:
        config: Configuration dictionary to validate

    Returns:
        True if valid

    Raises:
        ConfigValidationError: If validation fails
    """
    if not config:
        raise ConfigValidationError("Configuration cannot be empty")

    required_sections = ["sensors", "camera"]
    for section in required_sections:
        if section not in config:
            raise ConfigValidationError(f"Missing required section: {section}", section)

    # Validate each section
    if "sensors" in config:
        validate_sensor_config(config["sensors"])

    if "camera" in config:
        validate_camera_config(config["camera"])

    if "motion" in config:
        validate_motion_config(config["motion"])

    return True


def validate_sensor_config(config: Dict[str, Any]) -> bool:
    """
    Validate sensor configuration section.

    Checks:
    - read_interval is positive
    - temperature thresholds are valid (min < max)
    - humidity thresholds are in range 0-100
    """
    # TODO: Implement validation logic
    # Check read_interval > 0
    if config.get("read_interval", 1) <= 0:
        raise ConfigValidationError("read_interval must be positive", "read_interval")

    # Check temperature thresholds
    temp = config.get("temperature", {})
    if temp.get("min_threshold", 0) >= temp.get("max_threshold", 100):
        raise ConfigValidationError(
            "temperature min_threshold must be less than max_threshold",
            "temperature"
        )

    # Check humidity thresholds (0-100)
    humidity = config.get("humidity", {})
    if humidity.get("max_threshold", 100) > 100:
        raise ConfigValidationError(
            "humidity max_threshold must be <= 100",
            "humidity"
        )

    return True


def validate_camera_config(config: Dict[str, Any]) -> bool:
    """
    Validate camera configuration section.

    Checks:
    - resolution is [width, height] with positive values
    - framerate is between 1 and 120
    - rotation is 0, 90, 180, or 270
    """
    # Check resolution
    resolution = config.get("resolution", [1280, 720])
    if not isinstance(resolution, list) or len(resolution) != 2:
        raise ConfigValidationError("resolution must be [width, height]", "resolution")

    if any(v <= 0 for v in resolution):
        raise ConfigValidationError("resolution values must be positive", "resolution")

    # Check framerate
    framerate = config.get("framerate", 24)
    if not (1 <= framerate <= 120):
        raise ConfigValidationError("framerate must be between 1 and 120", "framerate")

    # Check rotation
    rotation = config.get("rotation", 0)
    if rotation not in [0, 90, 180, 270]:
        raise ConfigValidationError("rotation must be 0, 90, 180, or 270", "rotation")

    return True


def validate_motion_config(config: Dict[str, Any]) -> bool:
    """
    Validate motion detection configuration.

    Checks:
    - sensitivity is between 0 and 100
    - min_area is positive
    - recording_duration is positive
    """
    sensitivity = config.get("sensitivity", 50)
    if not (0 <= sensitivity <= 100):
        raise ConfigValidationError("sensitivity must be between 0 and 100", "sensitivity")

    min_area = config.get("min_area", 500)
    if min_area <= 0:
        raise ConfigValidationError("min_area must be positive", "min_area")

    duration = config.get("recording_duration", 30)
    if duration <= 0:
        raise ConfigValidationError("recording_duration must be positive", "recording_duration")

    return True


def validate_aws_config(config: Dict[str, Any]) -> bool:
    """
    Validate AWS configuration.

    Checks:
    - region is specified
    - S3 bucket name follows AWS naming rules
    - SNS topic ARN is valid format
    - IoT endpoint is not empty
    """
    if "region" not in config:
        raise ConfigValidationError("AWS region is required", "region")

    # Validate S3 bucket name (simplified)
    s3_config = config.get("s3", {})
    bucket = s3_config.get("bucket", "")
    if bucket and not bucket.islower() or any(c in bucket for c in "!@#$%^&*()"):
        raise ConfigValidationError("Invalid S3 bucket name format", "s3.bucket")

    # Validate SNS ARN format
    sns_config = config.get("sns", {})
    topic_arn = sns_config.get("topic_arn", "")
    if topic_arn and not topic_arn.startswith("arn:aws:sns:"):
        raise ConfigValidationError("Invalid SNS topic ARN format", "sns.topic_arn")

    # Validate IoT endpoint
    iot_config = config.get("iot", {})
    endpoint = iot_config.get("endpoint", "")
    if iot_config and not endpoint:
        raise ConfigValidationError("IoT endpoint cannot be empty", "iot.endpoint")

    return True
