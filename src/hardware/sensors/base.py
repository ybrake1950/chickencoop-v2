"""
Base sensor interface using Abstract Base Class.

Provides the BaseSensor ABC that all sensor implementations must extend.
"""

from abc import ABC, abstractmethod
from typing import Any

from .interface import Sensor


class BaseSensor(Sensor, ABC):
    """
    Abstract base class for all sensor implementations.

    All sensors must implement the read() method and provide a name property.
    This interface ensures consistent behavior across different sensor types
    and enables loose coupling through dependency injection.
    """

    def __init__(self, name: str = "sensor"):
        """Initialize sensor with a name."""
        self._name = name

    @property
    def name(self) -> str:
        """Get sensor name."""
        return self._name

    @abstractmethod
    def read(self) -> Any:
        """
        Read sensor data.

        Must be implemented by subclasses.

        Returns:
            Sensor reading data (type depends on implementation).
        """
        pass

    def is_available(self) -> bool:
        """
        Check if sensor is available and functioning.

        Returns:
            True if sensor is available, False otherwise.
        """
        return True
