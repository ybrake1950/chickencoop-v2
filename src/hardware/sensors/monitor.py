"""
Sensor monitoring service.

Provides SensorMonitor class for managing multiple sensors,
collecting readings, and detecting anomalies.
"""

from typing import Dict, List, Any
import logging

from .interface import Sensor


logger = logging.getLogger(__name__)


class SensorMonitor:
    """
    Monitors multiple sensors and detects anomalies.

    Manages sensor registration, periodic reading, and spike detection.
    """

    def __init__(self, read_interval: int = 300):
        """
        Initialize sensor monitor.

        Args:
            read_interval: Time in seconds between sensor reads (default: 300)
        """
        self.read_interval = read_interval
        self.sensors: List[Sensor] = []
        self.spike_thresholds: Dict[str, float] = {}
        self._previous_readings: Dict[str, float] = {}

    def register_sensor(self, sensor: Sensor) -> None:
        """
        Register a sensor for monitoring.

        Args:
            sensor: Sensor instance to register.
        """
        self.sensors.append(sensor)

    def read_all(self) -> Dict[str, Any]:
        """
        Read all registered sensors.

        Returns:
            Dictionary mapping sensor names to their readings.
            Failed sensors return None with optional error key.
        """
        readings = {}

        for sensor in self.sensors:
            try:
                reading = sensor.read()
                readings[sensor.name] = reading
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Failed to read sensor %s: %s", sensor.name, e)
                readings[sensor.name] = None
                readings[f"{sensor.name}_error"] = str(e)

        return readings

    def set_spike_threshold(self, sensor_type: str, threshold: float) -> None:
        """
        Set spike detection threshold for a sensor type.

        Args:
            sensor_type: Type of sensor (e.g., 'temperature', 'humidity')
            threshold: Maximum allowed change between readings
        """
        self.spike_thresholds[sensor_type] = threshold

    def is_spike(
        self, sensor_type: str, previous_value: float, current_value: float
    ) -> bool:
        """
        Detect if current reading represents a spike.

        Args:
            sensor_type: Type of sensor being checked
            previous_value: Previous sensor reading
            current_value: Current sensor reading

        Returns:
            True if change exceeds threshold, False otherwise.
        """
        if sensor_type not in self.spike_thresholds:
            return False

        threshold = self.spike_thresholds[sensor_type]
        change = abs(current_value - previous_value)

        return change > threshold
