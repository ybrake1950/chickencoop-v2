"""
Base sensor interface for hardware abstraction.

This module defines the abstract base class that all sensors must implement.
"""


class Sensor:
    """
    Abstract base class for all sensor implementations.

    All sensors must implement the read() method and provide a name property.
    """

    def __init__(self, name: str = "sensor"):
        """Initialize sensor with a name."""
        self._name = name

    @property
    def name(self) -> str:
        """Get sensor name."""
        return self._name

    def read(self):
        """
        Read sensor data.

        Must be implemented by subclasses.
        Raises NotImplementedError if called on base class.
        """
        raise NotImplementedError("Subclasses must implement read()")

    def is_available(self) -> bool:
        """
        Check if sensor is available and functioning.

        Returns:
            True if sensor is available, False otherwise.
        """
        return True


class SensorReadError(Exception):
    """Exception raised when sensor read operation fails."""
