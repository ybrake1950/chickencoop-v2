"""
TDD Tests: Sensor Interface

These tests define the expected behavior for the sensor abstraction layer.
Implement src/hardware/sensors/interface.py to make these tests pass.

Run: pytest tdd/phase2_hardware/sensors/test_sensor_interface.py -v
"""

import pytest
from unittest.mock import MagicMock, patch


# =============================================================================
# Test: Sensor Base Interface
# =============================================================================

class TestSensorInterface:
    """Tests for the base sensor interface."""

    def test_sensor_has_read_method(self):
        """All sensors must implement read() method."""
        from src.hardware.sensors.interface import Sensor

        sensor = Sensor()

        assert hasattr(sensor, 'read')
        assert callable(sensor.read)

    def test_sensor_has_name_property(self):
        """Sensors should have a name property."""
        from src.hardware.sensors.interface import Sensor

        sensor = Sensor()

        assert hasattr(sensor, 'name')

    def test_sensor_has_is_available_method(self):
        """Sensors should have is_available() method."""
        from src.hardware.sensors.interface import Sensor

        sensor = Sensor()

        assert hasattr(sensor, 'is_available')
        assert callable(sensor.is_available)

    def test_sensor_base_read_raises_not_implemented(self):
        """Base sensor read() should raise NotImplementedError."""
        from src.hardware.sensors.interface import Sensor

        sensor = Sensor()

        with pytest.raises(NotImplementedError):
            sensor.read()


# =============================================================================
# Test: Temperature Sensor
# =============================================================================

class TestTemperatureSensor:
    """Tests for temperature sensor implementation."""

    def test_temperature_sensor_inherits_interface(self):
        """TemperatureSensor should inherit from Sensor."""
        from src.hardware.sensors.interface import Sensor
        from src.hardware.sensors.temperature import TemperatureSensor

        sensor = TemperatureSensor()

        assert isinstance(sensor, Sensor)

    def test_temperature_sensor_read_returns_float(self, mock_i2c_bus):
        """read() should return a float temperature."""
        from src.hardware.sensors.temperature import TemperatureSensor

        with patch('src.hardware.sensors.temperature.smbus2') as mock_smbus:
            mock_smbus.SMBus.return_value = mock_i2c_bus
            sensor = TemperatureSensor()
            sensor._sensor = MagicMock(temperature=72.5)

            result = sensor.read()

            assert isinstance(result, float)

    def test_temperature_sensor_returns_fahrenheit_by_default(self, mock_temperature_sensor):
        """Default unit should be Fahrenheit."""
        from src.hardware.sensors.temperature import TemperatureSensor

        sensor = TemperatureSensor()
        sensor._sensor = mock_temperature_sensor

        result = sensor.read()

        # Assuming mock returns 72.5°F equivalent
        assert result > 32  # Sanity check for Fahrenheit

    def test_temperature_sensor_can_return_celsius(self, mock_temperature_sensor):
        """Should support Celsius unit."""
        from src.hardware.sensors.temperature import TemperatureSensor

        sensor = TemperatureSensor(unit="celsius")
        sensor._sensor = mock_temperature_sensor

        result = sensor.read()

        assert isinstance(result, float)

    def test_temperature_sensor_handles_read_error(self, mock_i2c_bus):
        """Should handle I2C read errors gracefully."""
        from src.hardware.sensors.temperature import TemperatureSensor, SensorReadError

        with patch('src.hardware.sensors.temperature.smbus2') as mock_smbus:
            mock_smbus.SMBus.return_value = mock_i2c_bus
            sensor = TemperatureSensor()
            sensor._sensor = MagicMock()
            sensor._sensor.temperature = property(lambda self: exec('raise IOError("I2C error")'))

            with pytest.raises(SensorReadError):
                sensor.read()


# =============================================================================
# Test: Humidity Sensor
# =============================================================================

class TestHumiditySensor:
    """Tests for humidity sensor implementation."""

    def test_humidity_sensor_read_returns_float(self, mock_temperature_sensor):
        """read() should return a float humidity percentage."""
        from src.hardware.sensors.humidity import HumiditySensor

        sensor = HumiditySensor()
        sensor._sensor = mock_temperature_sensor

        result = sensor.read()

        assert isinstance(result, float)

    def test_humidity_in_valid_range(self, mock_temperature_sensor):
        """Humidity should be between 0 and 100."""
        from src.hardware.sensors.humidity import HumiditySensor

        sensor = HumiditySensor()
        sensor._sensor = mock_temperature_sensor

        result = sensor.read()

        assert 0 <= result <= 100

    def test_humidity_sensor_name(self):
        """Humidity sensor should have correct name."""
        from src.hardware.sensors.humidity import HumiditySensor

        sensor = HumiditySensor()

        assert "humidity" in sensor.name.lower()


# =============================================================================
# Test: Combined Sensor (DHT/AHT)
# =============================================================================

class TestCombinedSensor:
    """Tests for combined temperature/humidity sensor."""

    def test_combined_sensor_reads_both(self, mock_temperature_sensor):
        """Combined sensor should read both temperature and humidity."""
        from src.hardware.sensors.combined import CombinedSensor

        sensor = CombinedSensor()
        sensor._sensor = mock_temperature_sensor

        result = sensor.read()

        assert "temperature" in result
        assert "humidity" in result

    def test_combined_sensor_returns_dict(self, mock_temperature_sensor):
        """Combined sensor should return dictionary."""
        from src.hardware.sensors.combined import CombinedSensor

        sensor = CombinedSensor()
        sensor._sensor = mock_temperature_sensor

        result = sensor.read()

        assert isinstance(result, dict)

    def test_combined_sensor_creates_reading_model(self, mock_temperature_sensor):
        """Should create SensorReading model."""
        from src.hardware.sensors.combined import CombinedSensor
        from src.models.sensor import SensorReading

        sensor = CombinedSensor(coop_id="test")
        sensor._sensor = mock_temperature_sensor

        result = sensor.read_as_model()

        assert isinstance(result, SensorReading)


# =============================================================================
# Test: Sensor Monitor
# =============================================================================

class TestSensorMonitor:
    """Tests for the sensor monitoring service."""

    def test_monitor_can_be_instantiated(self):
        """SensorMonitor should be instantiable."""
        from src.hardware.sensors.monitor import SensorMonitor

        monitor = SensorMonitor()

        assert monitor is not None

    def test_monitor_has_read_interval(self):
        """Monitor should have configurable read interval."""
        from src.hardware.sensors.monitor import SensorMonitor

        monitor = SensorMonitor(read_interval=300)

        assert monitor.read_interval == 300

    def test_monitor_registers_sensors(self):
        """Should be able to register sensors."""
        from src.hardware.sensors.monitor import SensorMonitor
        from src.hardware.sensors.interface import Sensor

        monitor = SensorMonitor()
        mock_sensor = MagicMock(spec=Sensor)

        monitor.register_sensor(mock_sensor)

        assert len(monitor.sensors) == 1

    def test_monitor_read_all_returns_dict(self):
        """read_all should return dictionary of readings."""
        from src.hardware.sensors.monitor import SensorMonitor

        monitor = SensorMonitor()
        mock_sensor = MagicMock()
        mock_sensor.name = "test_sensor"
        mock_sensor.read.return_value = 42.0

        monitor.register_sensor(mock_sensor)
        result = monitor.read_all()

        assert "test_sensor" in result
        assert result["test_sensor"] == 42.0

    def test_monitor_handles_sensor_failure(self):
        """Should handle individual sensor failures gracefully."""
        from src.hardware.sensors.monitor import SensorMonitor

        monitor = SensorMonitor()

        failing_sensor = MagicMock()
        failing_sensor.name = "failing"
        failing_sensor.read.side_effect = Exception("Sensor failed")

        working_sensor = MagicMock()
        working_sensor.name = "working"
        working_sensor.read.return_value = 72.5

        monitor.register_sensor(failing_sensor)
        monitor.register_sensor(working_sensor)

        result = monitor.read_all()

        # Working sensor should still return data
        assert "working" in result
        assert result["working"] == 72.5
        # Failing sensor should be marked as error
        assert "failing" in result
        assert result["failing"] is None or "error" in str(result.get("failing_error", ""))


# =============================================================================
# Test: Spike Detection
# =============================================================================

class TestSpikeDetection:
    """Tests for sensor spike detection."""

    def test_detect_temperature_spike(self):
        """Should detect sudden temperature changes."""
        from src.hardware.sensors.monitor import SensorMonitor

        monitor = SensorMonitor()
        monitor.set_spike_threshold("temperature", 10.0)

        # Simulate readings
        assert monitor.is_spike("temperature", 72.0, 73.0) is False
        assert monitor.is_spike("temperature", 72.0, 85.0) is True

    def test_detect_humidity_spike(self):
        """Should detect sudden humidity changes."""
        from src.hardware.sensors.monitor import SensorMonitor

        monitor = SensorMonitor()
        monitor.set_spike_threshold("humidity", 15.0)

        assert monitor.is_spike("humidity", 65.0, 67.0) is False
        assert monitor.is_spike("humidity", 65.0, 85.0) is True

    def test_spike_detection_configurable(self):
        """Spike thresholds should be configurable."""
        from src.hardware.sensors.monitor import SensorMonitor

        monitor = SensorMonitor()
        monitor.set_spike_threshold("temperature", 5.0)

        assert monitor.spike_thresholds["temperature"] == 5.0
