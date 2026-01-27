"""
Extended TDD Tests: Sensor Data Models (Coverage Improvement)

These tests add coverage for scenarios not covered in test_sensor_models.py.
Run: pytest tdd/phase1_foundation/models/test_sensor_models_extended.py -v
"""

import pytest
from datetime import datetime, timezone


# =============================================================================
# Test: Additional Serialization and BaseModel Methods
# =============================================================================

class TestSensorReadingExtendedSerialization:
    """Tests for additional serialization methods."""

    def test_to_json_returns_string(self):
        """to_json should return JSON string."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")
        result = reading.to_json()

        assert isinstance(result, str)
        assert "72.5" in result
        assert "65.0" in result
        assert "test" in result

    def test_from_json_creates_instance(self):
        """from_json should create SensorReading from JSON string."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")
        json_str = reading.to_json()

        new_reading = SensorReading.from_json(json_str)

        assert new_reading.temperature == 72.5
        assert new_reading.humidity == 65.0
        assert new_reading.coop_id == "test"

    def test_copy_creates_duplicate(self):
        """copy should create a duplicate instance."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")
        copy = reading.copy()

        assert copy.temperature == reading.temperature
        assert copy.humidity == reading.humidity
        assert copy.coop_id == reading.coop_id
        assert copy is not reading

    def test_timestamp_with_z_suffix(self):
        """Should handle timestamp strings with Z suffix."""
        from src.models.sensor import SensorReading

        # ISO format with Z for UTC
        reading = SensorReading(
            temperature=72.5,
            humidity=65.0,
            coop_id="test",
            timestamp="2025-01-25T14:30:00Z"
        )

        assert reading.timestamp.tzinfo == timezone.utc

    def test_timezone_naive_timestamp_gets_utc(self):
        """Timezone-naive timestamps should get UTC timezone."""
        from src.models.sensor import SensorReading

        naive_time = datetime(2025, 1, 25, 14, 30, 0)
        reading = SensorReading(
            temperature=72.5,
            humidity=65.0,
            coop_id="test",
            timestamp=naive_time
        )

        assert reading.timestamp.tzinfo == timezone.utc


# =============================================================================
# Test: Additional Validation Methods
# =============================================================================

class TestSensorReadingValidationExtended:
    """Tests for additional validation methods."""

    def test_is_valid_property_true_for_valid_reading(self):
        """is_valid should return True for valid reading."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")

        assert reading.is_valid is True

    def test_is_valid_property_false_for_invalid_reading(self):
        """is_valid should return False for invalid reading."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=150.0, coop_id="test")

        assert reading.is_valid is False

    def test_validation_errors_returns_empty_for_valid(self):
        """validation_errors should return empty list for valid reading."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")

        errors = reading.validation_errors()

        assert len(errors) == 0

    def test_validation_errors_returns_messages_for_invalid(self):
        """validation_errors should return error messages for invalid reading."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=150.0, coop_id="test")

        errors = reading.validation_errors()

        assert len(errors) > 0
        assert "humidity" in errors[0].lower()

    def test_humidity_at_zero_boundary(self):
        """Humidity at 0 should be valid."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=0.0, coop_id="test")

        assert reading.validate() is True

    def test_humidity_at_hundred_boundary(self):
        """Humidity at 100 should be valid."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=100.0, coop_id="test")

        assert reading.validate() is True

    def test_humidity_below_zero_invalid(self):
        """Humidity below 0 should be invalid."""
        from src.models.sensor import SensorReading, ValidationError

        reading = SensorReading(temperature=72.5, humidity=-1.0, coop_id="test")

        with pytest.raises(ValidationError):
            reading.validate()


# =============================================================================
# Test: Additional Anomaly Detection
# =============================================================================

class TestSensorReadingAnomalyExtended:
    """Tests for additional anomaly detection scenarios."""

    def test_normal_fahrenheit_not_anomalous(self):
        """Normal Fahrenheit temperature should not be anomalous."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=75.0, humidity=65.0, coop_id="test", unit="fahrenheit")

        assert reading.is_anomalous() is False

    def test_normal_celsius_not_anomalous(self):
        """Normal Celsius temperature should not be anomalous."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=25.0, humidity=65.0, coop_id="test", unit="celsius")

        assert reading.is_anomalous() is False

    def test_extreme_cold_fahrenheit_is_anomalous(self):
        """Temperature below -40°F should be anomalous."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=-50.0, humidity=65.0, coop_id="test", unit="fahrenheit")

        assert reading.is_anomalous() is True

    def test_extreme_hot_celsius_is_anomalous(self):
        """Temperature above 65°C should be anomalous."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=70.0, humidity=65.0, coop_id="test", unit="celsius")

        assert reading.is_anomalous() is True

    def test_extreme_cold_celsius_is_anomalous(self):
        """Temperature below -40°C should be anomalous."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=-45.0, humidity=65.0, coop_id="test", unit="celsius")

        assert reading.is_anomalous() is True


# =============================================================================
# Test: Temperature Conversion Edge Cases
# =============================================================================

class TestTemperatureConversionExtended:
    """Tests for temperature conversion edge cases."""

    def test_celsius_to_celsius_returns_same(self):
        """Celsius reading should return same value for temperature_celsius."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=25.0, humidity=65.0, coop_id="test", unit="celsius")

        assert reading.temperature_celsius == 25.0

    def test_fahrenheit_to_fahrenheit_returns_same(self):
        """Fahrenheit reading should return same value for temperature_fahrenheit."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test", unit="fahrenheit")

        assert reading.temperature_fahrenheit == 72.5


# =============================================================================
# Test: Comparison Edge Cases
# =============================================================================

class TestSensorReadingComparisonExtended:
    """Tests for comparison edge cases."""

    def test_equality_with_none(self):
        """Comparison with None should return False."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")

        assert (reading == None) is False

    def test_equality_with_different_type(self):
        """Comparison with different type should return False."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")

        assert (reading == "not a reading") is False
        assert (reading == 123) is False
        assert (reading == {"temp": 72.5}) is False

    def test_hash_works_in_set(self):
        """SensorReading should be hashable for use in sets."""
        from src.models.sensor import SensorReading

        reading1 = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")
        reading2 = SensorReading(temperature=73.0, humidity=64.0, coop_id="test")

        readings_set = {reading1, reading2}

        assert len(readings_set) == 2

    def test_str_representation(self):
        """__str__ should return readable string."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")

        str_repr = str(reading)

        assert "SensorReading" in str_repr
        assert "72.5" in str_repr

    def test_repr_representation(self):
        """__repr__ should return debug string."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")

        repr_str = repr(reading)

        assert "SensorReading" in repr_str
        assert "temperature" in repr_str


# =============================================================================
# Test: CSV Serialization Edge Cases
# =============================================================================

class TestCSVSerializationExtended:
    """Tests for CSV serialization edge cases."""

    def test_from_csv_row_with_extra_columns(self):
        """from_csv_row should handle rows with extra columns."""
        from src.models.sensor import SensorReading

        row = ["2025-01-25 14:30:00", "72.5", "65.0", "test", "extra1", "extra2"]
        reading = SensorReading.from_csv_row(row)

        assert reading.temperature == 72.5
        assert reading.humidity == 65.0
        assert reading.coop_id == "test"

    def test_csv_roundtrip_preserves_data(self):
        """Converting to CSV and back should preserve data."""
        from src.models.sensor import SensorReading

        original = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")
        csv_row = original.to_csv_row()
        restored = SensorReading.from_csv_row(csv_row)

        assert restored.temperature == original.temperature
        assert restored.humidity == original.humidity
        assert restored.coop_id == original.coop_id


# =============================================================================
# Test: Batch Extended Features
# =============================================================================

class TestSensorReadingBatchExtended:
    """Tests for additional batch features."""

    def test_batch_iteration(self):
        """Batch should support iteration."""
        from src.models.sensor import SensorReading, SensorReadingBatch

        readings = [
            SensorReading(temperature=70.0, humidity=65.0, coop_id="test"),
            SensorReading(temperature=75.0, humidity=64.0, coop_id="test"),
            SensorReading(temperature=80.0, humidity=63.0, coop_id="test"),
        ]
        batch = SensorReadingBatch(readings)

        count = 0
        for reading in batch:
            assert isinstance(reading, SensorReading)
            count += 1

        assert count == 3

    def test_batch_readings_property(self):
        """Batch should have readings property."""
        from src.models.sensor import SensorReading, SensorReadingBatch

        readings = [
            SensorReading(temperature=70.0, humidity=65.0, coop_id="test"),
            SensorReading(temperature=80.0, humidity=64.0, coop_id="test"),
        ]
        batch = SensorReadingBatch(readings)

        assert batch.readings == readings
        assert len(batch.readings) == 2

    def test_batch_min_humidity(self):
        """Batch should calculate minimum humidity."""
        from src.models.sensor import SensorReading, SensorReadingBatch

        readings = [
            SensorReading(temperature=72.5, humidity=60.0, coop_id="test"),
            SensorReading(temperature=72.5, humidity=70.0, coop_id="test"),
            SensorReading(temperature=72.5, humidity=55.0, coop_id="test"),
        ]
        batch = SensorReadingBatch(readings)

        assert batch.min_humidity == 55.0

    def test_batch_max_humidity(self):
        """Batch should calculate maximum humidity."""
        from src.models.sensor import SensorReading, SensorReadingBatch

        readings = [
            SensorReading(temperature=72.5, humidity=60.0, coop_id="test"),
            SensorReading(temperature=72.5, humidity=85.0, coop_id="test"),
            SensorReading(temperature=72.5, humidity=70.0, coop_id="test"),
        ]
        batch = SensorReadingBatch(readings)

        assert batch.max_humidity == 85.0

    def test_empty_batch_min_humidity(self):
        """Empty batch should return 0.0 for min_humidity."""
        from src.models.sensor import SensorReadingBatch

        batch = SensorReadingBatch([])

        assert batch.min_humidity == 0.0

    def test_empty_batch_max_humidity(self):
        """Empty batch should return 0.0 for max_humidity."""
        from src.models.sensor import SensorReadingBatch

        batch = SensorReadingBatch([])

        assert batch.max_humidity == 0.0

    def test_empty_batch_average_temperature(self):
        """Empty batch should return 0.0 for average_temperature."""
        from src.models.sensor import SensorReadingBatch

        batch = SensorReadingBatch([])

        assert batch.average_temperature == 0.0

    def test_empty_batch_average_humidity(self):
        """Empty batch should return 0.0 for average_humidity."""
        from src.models.sensor import SensorReadingBatch

        batch = SensorReadingBatch([])

        assert batch.average_humidity == 0.0

    def test_empty_batch_min_temperature(self):
        """Empty batch should return 0.0 for min_temperature."""
        from src.models.sensor import SensorReadingBatch

        batch = SensorReadingBatch([])

        assert batch.min_temperature == 0.0

    def test_empty_batch_max_temperature(self):
        """Empty batch should return 0.0 for max_temperature."""
        from src.models.sensor import SensorReadingBatch

        batch = SensorReadingBatch([])

        assert batch.max_temperature == 0.0

    def test_empty_batch_length(self):
        """Empty batch should have length 0."""
        from src.models.sensor import SensorReadingBatch

        batch = SensorReadingBatch([])

        assert len(batch) == 0

    def test_empty_batch_iteration(self):
        """Empty batch should support iteration with no items."""
        from src.models.sensor import SensorReadingBatch

        batch = SensorReadingBatch([])

        count = 0
        for reading in batch:
            count += 1

        assert count == 0


# =============================================================================
# Test: Unit Parameter Handling
# =============================================================================

class TestUnitParameterHandling:
    """Tests for unit parameter handling."""

    def test_default_unit_is_fahrenheit(self):
        """Default unit should be fahrenheit."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=72.5, humidity=65.0, coop_id="test")

        assert reading.unit == "fahrenheit"

    def test_celsius_unit_parameter(self):
        """Should accept celsius as unit parameter."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=22.5, humidity=65.0, coop_id="test", unit="celsius")

        assert reading.unit == "celsius"

    def test_unit_preserved_in_dict(self):
        """Unit should be preserved in to_dict."""
        from src.models.sensor import SensorReading

        reading = SensorReading(temperature=22.5, humidity=65.0, coop_id="test", unit="celsius")
        data = reading.to_dict()

        assert data["unit"] == "celsius"
