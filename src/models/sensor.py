"""
Sensor data models for Chicken Coop application.

This module provides models for sensor readings and batch operations.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from .base import BaseModel, ValidationError


class SensorReading(BaseModel):
    """
    Represents a single sensor reading.

    Attributes:
        temperature: Temperature value
        humidity: Humidity percentage (0-100)
        coop_id: Identifier for the coop
        timestamp: When the reading was taken (UTC)
        unit: Temperature unit ('fahrenheit' or 'celsius')
    """

    temperature: float
    humidity: float
    coop_id: str
    timestamp: datetime
    unit: str

    def __init__(
        self,
        temperature: float,
        humidity: float,
        coop_id: str,
        timestamp: Optional[datetime] = None,
        unit: str = "fahrenheit",
        **kwargs
    ):
        super().__init__(**kwargs)

        # Type validation
        if not isinstance(temperature, (int, float)):
            raise TypeError("temperature must be numeric")
        if not isinstance(humidity, (int, float)):
            raise TypeError("humidity must be numeric")
        if not isinstance(coop_id, str):
            raise TypeError("coop_id must be a string")

        self.temperature = float(temperature)
        self.humidity = float(humidity)
        self.coop_id = coop_id
        self.unit = unit

        if timestamp:
            # Handle timestamp as string (ISO format) or datetime object
            if isinstance(timestamp, str):
                self.timestamp = datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                )
            else:
                self.timestamp = timestamp
        else:
            self.timestamp = datetime.now(timezone.utc)

        # Ensure timestamp is UTC
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)

    def validate(self) -> bool:
        """Validate sensor reading values."""
        if not (0 <= self.humidity <= 100):
            raise ValidationError("humidity must be between 0 and 100", "humidity")
        return True

    def __eq__(self, other: object) -> bool:
        """Check equality based on sensor data, not metadata."""
        if other is None:
            return False
        if not isinstance(other, SensorReading):
            return False
        return (
            self.temperature == other.temperature
            and self.humidity == other.humidity
            and self.coop_id == other.coop_id
            and self.timestamp == other.timestamp
            and self.unit == other.unit
        )

    def __hash__(self) -> int:
        """Generate hash based on sensor data for use in sets/dicts."""
        return hash(
            (self.temperature, self.humidity, self.coop_id, self.timestamp, self.unit)
        )

    def is_anomalous(self) -> bool:
        """Check if reading has anomalous values."""
        # Temperature sanity check (Fahrenheit)
        if self.unit == "fahrenheit":
            if self.temperature < -40 or self.temperature > 150:
                return True
        else:  # Celsius
            if self.temperature < -40 or self.temperature > 65:
                return True

        return False

    @property
    def temperature_celsius(self) -> float:
        """Get temperature in Celsius."""
        if self.unit == "celsius":
            return self.temperature
        return (self.temperature - 32) * 5 / 9

    @property
    def temperature_fahrenheit(self) -> float:
        """Get temperature in Fahrenheit."""
        if self.unit == "fahrenheit":
            return self.temperature
        return (self.temperature * 9 / 5) + 32

    def to_csv_row(self) -> Tuple:
        """Convert to CSV row format."""
        return (
            self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            str(self.temperature),
            str(self.humidity),
            self.coop_id,
        )

    @classmethod
    def from_csv_row(cls, row: List[str]) -> "SensorReading":
        """Create from CSV row."""
        timestamp_str, temp_str, humidity_str, coop_id = row[:4]
        return cls(
            temperature=float(temp_str),
            humidity=float(humidity_str),
            coop_id=coop_id,
            timestamp=datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            ),
        )


class SensorReadingBatch:
    """
    Collection of sensor readings with aggregate calculations.

    Provides statistics like averages, min/max values.
    """

    def __init__(self, readings: List[SensorReading]):
        """Initialize batch with a list of sensor readings.

        Args:
            readings: List of SensorReading instances.
        """
        self._readings = readings

    def __len__(self) -> int:
        return len(self._readings)

    def __iter__(self):
        return iter(self._readings)

    @property
    def readings(self) -> List[SensorReading]:
        """Get all readings."""
        return self._readings

    @property
    def average_temperature(self) -> float:
        """Calculate average temperature."""
        if not self._readings:
            return 0.0
        return sum(r.temperature for r in self._readings) / len(self._readings)

    @property
    def average_humidity(self) -> float:
        """Calculate average humidity."""
        if not self._readings:
            return 0.0
        return sum(r.humidity for r in self._readings) / len(self._readings)

    @property
    def min_temperature(self) -> float:
        """Get minimum temperature."""
        if not self._readings:
            return 0.0
        return min(r.temperature for r in self._readings)

    @property
    def max_temperature(self) -> float:
        """Get maximum temperature."""
        if not self._readings:
            return 0.0
        return max(r.temperature for r in self._readings)

    @property
    def min_humidity(self) -> float:
        """Get minimum humidity."""
        if not self._readings:
            return 0.0
        return min(r.humidity for r in self._readings)

    @property
    def max_humidity(self) -> float:
        """Get maximum humidity."""
        if not self._readings:
            return 0.0
        return max(r.humidity for r in self._readings)
