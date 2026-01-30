"""Custom exception hierarchy for the ChickenCoop application."""


class ChickenCoopError(Exception):
    """Base exception for all ChickenCoop errors."""

    def __init__(self, message: str = "", **kwargs):
        self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)
        super().__init__(message)


class SensorError(ChickenCoopError):
    """Raised for sensor-related errors."""

    def __init__(self, message: str = "", sensor_name: str = "", **kwargs):
        self.sensor_name = sensor_name
        display = f"{message} [{sensor_name}]" if sensor_name else message
        super().__init__(display, **kwargs)


class AWSError(ChickenCoopError):
    """Raised for AWS service errors."""
    pass


class ValidationError(ChickenCoopError):
    """Raised for data validation errors."""
    pass


class ConfigurationError(ChickenCoopError):
    """Raised for configuration errors."""
    pass
