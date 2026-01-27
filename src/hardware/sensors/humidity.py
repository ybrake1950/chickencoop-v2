"""
Humidity sensor implementation.

Provides HumiditySensor class for reading humidity data via I2C.
"""

from .interface import Sensor, SensorReadError

try:
    import smbus2
    import adafruit_ahtx0
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False


class HumiditySensor(Sensor):
    """
    Humidity sensor implementation using AHT20/AHT10 sensor.

    Returns relative humidity as a percentage (0-100).
    """

    def __init__(self, bus_number: int = 1):
        """
        Initialize humidity sensor.

        Args:
            bus_number: I2C bus number (default: 1)
        """
        super().__init__(name="humidity")
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

    def read(self) -> float:
        """
        Read humidity from sensor.

        Returns:
            Humidity percentage as float (0-100).

        Raises:
            SensorReadError: If sensor read fails.
        """
        if self._sensor is None:
            raise SensorReadError("Sensor not initialized")

        try:
            # Read relative humidity from sensor
            humidity = self._sensor.relative_humidity

            # Ensure value is in valid range
            humidity = max(0.0, min(100.0, humidity))

            return float(humidity)

        except (IOError, OSError, AttributeError) as e:
            raise SensorReadError(f"Failed to read humidity: {e}")

    def is_available(self) -> bool:
        """Check if humidity sensor is available."""
        return self._sensor is not None
