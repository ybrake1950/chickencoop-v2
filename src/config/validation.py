"""Configuration validation for chickencoop application."""

import re
from typing import Any, Dict


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate the full application configuration.

    Args:
        config: Configuration dictionary to validate

    Returns:
        True if configuration is valid

    Raises:
        ConfigValidationError: If configuration is invalid or missing required sections
    """
    if not config:
        raise ConfigValidationError("Configuration cannot be empty")

    if "sensors" not in config:
        raise ConfigValidationError("Missing required section: sensors")

    if "camera" not in config:
        raise ConfigValidationError("Missing required section: camera")

    return True


def validate_sensor_config(config: Dict[str, Any]) -> bool:
    """
    Validate sensor configuration.

    Args:
        config: Sensor configuration dictionary

    Returns:
        True if configuration is valid

    Raises:
        ConfigValidationError: If read_interval or thresholds are invalid
    """
    if config.get("read_interval", 1) <= 0:
        raise ConfigValidationError("read_interval must be positive")

    temp = config.get("temperature", {})
    if temp.get("min_threshold", 0) >= temp.get("max_threshold", 1):
        raise ConfigValidationError(
            "temperature min_threshold must be less than max_threshold"
        )

    humidity = config.get("humidity", {})
    min_h = humidity.get("min_threshold", 0)
    max_h = humidity.get("max_threshold", 100)
    if min_h < 0 or min_h > 100 or max_h < 0 or max_h > 100:
        raise ConfigValidationError("humidity thresholds must be between 0 and 100")

    return True


def validate_camera_config(config: Dict[str, Any]) -> bool:
    """
    Validate camera configuration.

    Args:
        config: Camera configuration dictionary

    Returns:
        True if configuration is valid

    Raises:
        ConfigValidationError: If resolution, framerate, or rotation are invalid
    """
    resolution = config.get("resolution", [])
    if not isinstance(resolution, list) or len(resolution) != 2:
        raise ConfigValidationError("resolution must be a list of two integers")

    if resolution[0] <= 0 or resolution[1] <= 0:
        raise ConfigValidationError("resolution values must be positive")

    framerate = config.get("framerate", 1)
    if framerate < 1 or framerate > 120:
        raise ConfigValidationError("framerate must be between 1 and 120")

    rotation = config.get("rotation", 0)
    if rotation not in (0, 90, 180, 270):
        raise ConfigValidationError("rotation must be 0, 90, 180, or 270")

    return True


def validate_motion_config(config: Dict[str, Any]) -> bool:
    """
    Validate motion detection configuration.

    Args:
        config: Motion detection configuration dictionary

    Returns:
        True if configuration is valid

    Raises:
        ConfigValidationError: If sensitivity, min_area, or recording_duration are invalid
    """
    sensitivity = config.get("sensitivity", 50)
    if sensitivity < 0 or sensitivity > 100:
        raise ConfigValidationError("sensitivity must be between 0 and 100")

    min_area = config.get("min_area", 1)
    if min_area <= 0:
        raise ConfigValidationError("min_area must be positive")

    recording_duration = config.get("recording_duration", 1)
    if recording_duration <= 0:
        raise ConfigValidationError("recording_duration must be positive")

    return True


def validate_aws_config(config: Dict[str, Any]) -> bool:
    """
    Validate AWS configuration.

    Args:
        config: AWS configuration dictionary

    Returns:
        True if configuration is valid

    Raises:
        ConfigValidationError: If region is missing or S3/SNS/IoT settings are invalid
    """
    if "region" not in config:
        raise ConfigValidationError("AWS config must specify a region")

    s3 = config.get("s3", {})
    bucket = s3.get("bucket", "")
    if bucket:
        if not re.match(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", bucket):
            raise ConfigValidationError("Invalid S3 bucket name format")

    sns = config.get("sns", {})
    topic_arn = sns.get("topic_arn", "")
    if topic_arn:
        if not topic_arn.startswith("arn:aws:sns:"):
            raise ConfigValidationError("Invalid SNS topic ARN format")

    iot = config.get("iot", {})
    endpoint = iot.get("endpoint", "")
    if "endpoint" in iot and not endpoint:
        raise ConfigValidationError("IoT endpoint must be a valid hostname")

    return True
