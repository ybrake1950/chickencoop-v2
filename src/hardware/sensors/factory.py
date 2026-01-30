"""Factory for creating sensor instances."""

from src.hardware.sensors.temperature import TemperatureSensor
from src.hardware.sensors.humidity import HumiditySensor
from src.hardware.sensors.combined import CombinedSensor


class SensorFactory:
    """Factory for creating sensor instances by type."""

    def create(self, sensor_type: str, **kwargs):
        """Create a sensor instance by type.

        Args:
            sensor_type: Type of sensor ('temperature', 'humidity', 'combined').

        Returns:
            Sensor instance.
        """
        if sensor_type == "temperature":
            return TemperatureSensor(**kwargs)
        elif sensor_type == "humidity":
            return HumiditySensor(**kwargs)
        elif sensor_type == "combined":
            return CombinedSensor(**kwargs)
        else:
            raise ValueError(f"Unknown sensor type: {sensor_type}")
