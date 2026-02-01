"""
Environment variable handling utilities.

Provides typed access to environment variables with defaults,
validation, and special handling for common configuration values.
"""

import os
from typing import Optional


class MissingEnvironmentVariable(Exception):
    """Raised when a required environment variable is not set."""


def get_env(
    name: str, default: Optional[str] = None, required: bool = False
) -> Optional[str]:
    """
    Get an environment variable value.

    Args:
        name: Name of the environment variable
        default: Default value if not set
        required: If True, raise exception when not set

    Returns:
        The environment variable value or default

    Raises:
        MissingEnvironmentVariable: If required and not set
    """
    value = os.environ.get(name)

    if value is None:
        if required:
            raise MissingEnvironmentVariable(
                f"Required environment variable not set: {name}"
            )
        return default

    return value


def get_env_int(name: str, default: Optional[int] = None) -> Optional[int]:
    """
    Get an environment variable as an integer.

    Args:
        name: Name of the environment variable
        default: Default value if not set

    Returns:
        The environment variable value as integer, or default if not set
    """
    value = os.environ.get(name)

    if value is None:
        return default

    return int(value)


def get_env_float(name: str, default: Optional[float] = None) -> Optional[float]:
    """
    Get an environment variable as a float.

    Args:
        name: Name of the environment variable
        default: Default value if not set

    Returns:
        The environment variable value as float, or default if not set
    """
    value = os.environ.get(name)

    if value is None:
        return default

    return float(value)


def get_env_bool(name: str, default: bool = False) -> bool:
    """
    Get an environment variable as a boolean.

    Truthy values: 'true', '1', 'yes' (case-insensitive).
    All other values are treated as falsy.

    Args:
        name: Name of the environment variable
        default: Default value if not set

    Returns:
        The environment variable value as boolean, or default if not set
    """
    value = os.environ.get(name)

    if value is None:
        return default

    return value.lower() in ("true", "1", "yes")


def get_coop_id() -> str:
    """
    Get the COOP_ID environment variable.

    Returns normalized (lowercase) coop ID, defaults to 'default'.
    """
    coop_id = os.environ.get("COOP_ID", "default")
    return coop_id.lower()


def is_testing() -> bool:
    """Check if running in test mode."""
    return get_env_bool("TESTING", default=False)


def is_production() -> bool:
    """Check if running in production mode."""
    return not is_testing()


def get_secret_key() -> str:
    """
    Get the SECRET_KEY for Flask sessions.

    In testing mode, returns a default test key.
    In production, requires the environment variable to be set.

    Raises:
        MissingEnvironmentVariable: If not set in production
    """
    if is_testing():
        return os.environ.get("SECRET_KEY", "test-secret-key-not-for-production")

    value = os.environ.get("SECRET_KEY")
    if value is None:
        raise MissingEnvironmentVariable("SECRET_KEY must be set in production")

    return value


def get_aws_region() -> Optional[str]:
    """
    Get the AWS region.

    Checks AWS_REGION first, then AWS_DEFAULT_REGION, defaults to 'us-east-1'.
    """
    return os.environ.get("AWS_REGION") or os.environ.get(
        "AWS_DEFAULT_REGION", "us-east-1"
    )
