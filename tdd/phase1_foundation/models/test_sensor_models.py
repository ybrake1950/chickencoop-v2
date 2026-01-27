"""
TDD Tests: Sensor Data Models

These tests define the expected behavior for sensor reading models.
Implement src/models/sensor.py to make these tests pass.

Run: pytest tdd/phase1_foundation/models/test_sensor_models.py -v
"""

import pytest
from datetime import datetime, timezone


# =============================================================================
# Test: SensorReading Model
# =============================================================================

class TestSensorReadingModel:
    """Tests for the SensorReading model."""

    def test_sensor_reading_requires_temperature(self):
        """SensorReading must have temperature."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")

        assert reading.temperature == 72.5

    def test_sensor_reading_requires_humidity(self):
        """SensorReading must have humidity."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")

        assert reading.humidity == 65.0

    def test_sensor_reading_requires_coop_id(self):
        """SensorReading must have coop_id."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="coop1")

        assert reading.coop_id == "coop1"

    def test_sensor_reading_has_timestamp(self):
        """SensorReading should have a timestamp."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")

        assert hasattr(reading, 'timestamp')
        assert isinstance(reading.timestamp, datetime)

    def test_sensor_reading_timestamp_is_utc(self):
        """SensorReading timestamp should be UTC."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")

        assert reading.timestamp.tzinfo == timezone.utc

    def test_sensor_reading_custom_timestamp(self):
        """SensorReading should accept custom timestamp."""
        from src.models.sensor import SensorReading

        custom_time = datetime(2025, 1, 25, 14, 30, 0, tzinfo=timezone.utc)
        reading = SensorReading(
            temperature=72.5,
            humidity=65.0,
            coop_id="test",
            timestamp=custom_time
        )

        assert reading.timestamp == custom_time


# =============================================================================
# Test: SensorReading Validation
# =============================================================================

class TestSensorReadingValidation:
    """Tests for SensorReading validation."""

    def test_temperature_must_be_numeric(self):
        """Temperature must be a number."""
        from src.models.sensor import SensorReading, ValidationError

        with pytest.raises((ValidationError, TypeError, ValueError)):
            SensorReading(temperature="hot", humidity=65.0, coop_id="test")

    def test_humidity_must_be_numeric(self):
        """Humidity must be a number."""
        from src.models.sensor import SensorReading, ValidationError

        with pytest.raises((ValidationError, TypeError, ValueError)):
            SensorReading(temperature=72.5, humidity="wet", coop_id="test")

    def test_humidity_must_be_in_range(self):
        """Humidity must be between 0 and 100."""
        from src.models.sensor import SensorReading, ValidationError

        with pytest.raises(ValidationError):
            reading = SensorReading(temperature=72.5, humidity=150.0, coop_id="test")
            reading.validate()

    def test_temperature_reasonable_range_warning(self):
        """Extreme temperatures should trigger a warning or flag."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=200.0, humidity=65.0, coop_id="test")

        # Should have a method to check if reading is anomalous
        assert reading.is_anomalous() or hasattr(reading, 'warnings')

    def test_coop_id_must_be_string(self):
        """Coop ID must be a string."""
        from src.models.sensor import SensorReading, ValidationError

        with pytest.raises((ValidationError, TypeError)):
            SensorReading(temperature=72.5, humidity=65.0, coop_id=123)


# =============================================================================
# Test: SensorReading Serialization
# =============================================================================

class TestSensorReadingSerialization:
    """Tests for SensorReading serialization."""

    def test_to_dict_includes_all_fields(self):
        """to_dict should include all fields."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")
        result = reading.to_dict()

        assert "temperature" in result
        assert "humidity" in result
        assert "coop_id" in result
        assert "timestamp" in result

    def test_to_csv_row_returns_list(self):
        """to_csv_row should return list of values."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")
        result = reading.to_csv_row()

        assert isinstance(result, (list, tuple))
        assert len(result) >= 4  # timestamp, temp, humidity, coop_id

    def test_from_dict_creates_instance(self):
        """from_dict should create SensorReading."""
        from src.models.sensor import SensorReading

        data = {
            "temperature": 72.5,
            "humidity": 65.0,
            "coop_id": "test",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        reading = SensorReading.from_dict(data)

        assert reading.temperature == 72.5
        assert reading.humidity == 65.0

    def test_from_csv_row_creates_instance(self):
        """from_csv_row should create SensorReading."""
        from src.models.sensor import SensorReading

        row = ["2025-01-25 14:30:00", "72.5", "65.0", "test"]
        reading = SensorReading.from_csv_row(row)

        assert reading.temperature == 72.5
        assert reading.humidity == 65.0


# =============================================================================
# Test: SensorReading Comparison
# =============================================================================

class TestSensorReadingComparison:
    """Tests for SensorReading comparison."""

    def test_readings_with_same_values_are_equal(self):
        """Readings with same values should be equal."""
        from src.models.sensor import SensorReading

        timestamp = datetime.now(timezone.utc)
        reading1 = SensorReading(
            temperature=72.5, humidity=65.0, coop_id="test", timestamp=timestamp
        )
        reading2 = SensorReading(
            temperature=72.5, humidity=65.0, coop_id="test", timestamp=timestamp
        )

        assert reading1 == reading2

    def test_readings_with_different_values_not_equal(self):
        """Readings with different values should not be equal."""
        from src.models.sensor import SensorReading

        reading1 = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")
        reading2 = SensorReading(temperature=75.0, humidity=65.0, coop_id="test")

        assert reading1 != reading2


# =============================================================================
# Test: Temperature Unit Conversion
# =============================================================================

class TestTemperatureConversion:
    """Tests for temperature unit conversion."""

    def test_to_celsius_converts_fahrenheit(self):
        """Should convert Fahrenheit to Celsius."""
        from src.models.sensor import SensorReading

        reading = SensorReading(
            temperature=72.5, humidity=65.0, coop_id="test", unit="fahrenheit"
        )
        celsius = reading.temperature_celsius

        assert abs(celsius - 22.5) < 0.1  # 72.5F ≈ 22.5C

    def test_to_fahrenheit_converts_celsius(self):
        """Should convert Celsius to Fahrenheit."""
        from src.models.sensor import SensorReading

        reading = SensorReading(
            temperature=22.5, humidity=65.0, coop_id="test", unit="celsius"
        )
        fahrenheit = reading.temperature_fahrenheit

        assert abs(fahrenheit - 72.5) < 0.1  # 22.5C ≈ 72.5F


# =============================================================================
# Test: SensorReadingBatch Model
# =============================================================================

class TestSensorReadingBatch:
    """Tests for batched sensor readings."""

    def test_batch_can_hold_multiple_readings(self):
        """Batch should hold multiple readings."""
        from src.models.sensor import SensorReading, SensorReadingBatch

        readings = [
            SensorReading(temperature=72.5, humidity=65.0, coop_id="test"),
            SensorReading(temperature=73.0, humidity=64.0, coop_id="test"),
        ]
        batch = SensorReadingBatch(readings)

        assert len(batch) == 2

    def test_batch_average_temperature(self):
        """Batch should calculate average temperature."""
        from src.models.sensor import SensorReading, SensorReadingBatch

        readings = [
            SensorReading(temperature=70.0, humidity=65.0, coop_id="test"),
            SensorReading(temperature=80.0, humidity=65.0, coop_id="test"),
        ]
        batch = SensorReadingBatch(readings)

        assert batch.average_temperature == 75.0

    def test_batch_average_humidity(self):
        """Batch should calculate average humidity."""
        from src.models.sensor import SensorReading, SensorReadingBatch

        readings = [
            SensorReading(temperature=72.5, humidity=60.0, coop_id="test"),
            SensorReading(temperature=72.5, humidity=70.0, coop_id="test"),
        ]
        batch = SensorReadingBatch(readings)

        assert batch.average_humidity == 65.0

    def test_batch_min_max_temperature(self):
        """Batch should track min/max temperature."""
        from src.models.sensor import SensorReading, SensorReadingBatch

        readings = [
            SensorReading(temperature=70.0, humidity=65.0, coop_id="test"),
            SensorReading(temperature=75.0, humidity=65.0, coop_id="test"),
            SensorReading(temperature=80.0, humidity=65.0, coop_id="test"),
        ]
        batch = SensorReadingBatch(readings)

        assert batch.min_temperature == 70.0
        assert batch.max_temperature == 80.0
