"""
Combined sensor implementation for temperature and humidity.

Provides CombinedSensor class that reads both temperature and humidity
from a single sensor device (DHT or AHT series).
"""

from typing import Dict
from datetime import datetime, timezone

from .interface import Sensor, SensorReadError
from src.models.sensor import SensorReading

try:
    import smbus2
    import adafruit_ahtx0
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False


class CombinedSensor(Sensor):
    """
    Combined temperature and humidity sensor.

    Reads both temperature and humidity from AHT20/AHT10 sensor.
    """

    def __init__(self, unit: str = "fahrenheit", bus_number: int = 1, coop_id: str = "default"):
        """
        Initialize combined sensor.

        Args:
            unit: Temperature unit ('fahrenheit' or 'celsius')
            bus_number: I2C bus number (default: 1)
            coop_id: Identifier for the coop
        """
        super().__init__(name="combined_temp_humidity")
        self.unit = unit
        self.coop_id = coop_id
        self._sensor = None

        if HAS_HARDWARE:
            try:
                import board
                import busio
                i2c = busio.I2C(board.SCL, board.SDA)
                self._sensor = adafruit_ahtx0.AHTx0(i2c)
            except Exception:
                # If hardware initialization fails, leave _sensor as None
                pass

    def read(self) -> Dict[str, float]:
        """
        Read both temperature and humidity from sensor.

        Returns:
            Dictionary with 'temperature' and 'humidity' keys.

        Raises:
            SensorReadError: If sensor read fails.
        """
        if self._sensor is None:
            raise SensorReadError("Sensor not initialized")

        try:
            # Read temperature from sensor
            temp_celsius = self._sensor.temperature
            humidity = self._sensor.relative_humidity

            # Convert temperature to requested unit
            if self.unit == "celsius":
                temperature = float(temp_celsius)
            else:  # fahrenheit (default)
                temperature = float((temp_celsius * 9/5) + 32)

            # Ensure humidity is in valid range
            humidity = max(0.0, min(100.0, humidity))

            return {
                "temperature": temperature,
                "humidity": float(humidity)
            }

        except (IOError, OSError, AttributeError) as e:
            raise SensorReadError(f"Failed to read sensor: {e}")

    def read_as_model(self) -> SensorReading:
        """
        Read sensor data and return as SensorReading model.

        Returns:
            SensorReading instance with current readings.

        Raises:
            SensorReadError: If sensor read fails.
        """
        data = self.read()

        return SensorReading(
            temperature=data["temperature"],
            humidity=data["humidity"],
            coop_id=self.coop_id,
            timestamp=datetime.now(timezone.utc),
            unit=self.unit
        )

    def is_available(self) -> bool:
        """Check if combined sensor is available."""
        return self._sensor is not None
