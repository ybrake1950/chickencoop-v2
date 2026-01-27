"""
Temperature sensor implementation.

Provides TemperatureSensor class for reading temperature data via I2C.
"""

from .interface import Sensor, SensorReadError

try:
    import smbus2
    import adafruit_ahtx0
    HAS_HARDWARE = True
except ImportError:
    smbus2 = None
    adafruit_ahtx0 = None
    HAS_HARDWARE = False


class TemperatureSensor(Sensor):
    """
    Temperature sensor implementation using AHT20/AHT10 sensor.

    Supports both Fahrenheit and Celsius readings.
    """

    def __init__(self, unit: str = "fahrenheit", bus_number: int = 1):
        """
        Initialize temperature sensor.

        Args:
            unit: Temperature unit ('fahrenheit' or 'celsius')
            bus_number: I2C bus number (default: 1)
        """
        super().__init__(name="temperature")
        self.unit = unit
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
        Read temperature from sensor.

        Returns:
            Temperature as float in configured unit.

        Raises:
            SensorReadError: If sensor read fails.
        """
        if self._sensor is None:
            raise SensorReadError("Sensor not initialized")

        try:
            # Read temperature from sensor
            temp_celsius = self._sensor.temperature

            # Convert to requested unit
            if self.unit == "celsius":
                return float(temp_celsius)
            else:  # fahrenheit (default)
                return float((temp_celsius * 9/5) + 32)

        except (IOError, OSError, AttributeError, TypeError) as e:
            raise SensorReadError(f"Failed to read temperature: {e}")

    def is_available(self) -> bool:
        """Check if temperature sensor is available."""
        return self._sensor is not None
