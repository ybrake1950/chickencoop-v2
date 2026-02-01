"""Coverage improvement tests for sensor hardware modules.

Covers:
- src/hardware/sensors/humidity.py (60% -> 80%+)
- src/hardware/sensors/temperature.py (69% -> 80%+)
- src/hardware/sensors/combined.py (71% -> 80%+)
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from src.hardware.sensors.humidity import HumiditySensor
from src.hardware.sensors.temperature import TemperatureSensor
from src.hardware.sensors.combined import CombinedSensor
from src.hardware.sensors.interface import SensorReadError


class TestHumiditySensorInit:
    def test_init_with_hardware_success(self):
        """Test hardware initialization when HAS_HARDWARE is True."""
        mock_i2c = MagicMock()
        mock_sensor = MagicMock()
        mock_board = MagicMock()
        mock_busio = MagicMock()
        mock_busio.I2C.return_value = mock_i2c
        mock_ahtx0 = MagicMock()
        mock_ahtx0.AHTx0.return_value = mock_sensor

        with patch.dict(
            "sys.modules",
            {
                "board": mock_board,
                "busio": mock_busio,
                "adafruit_ahtx0": mock_ahtx0,
            },
        ):
            import importlib
            import src.hardware.sensors.humidity as hmod

            with patch.object(hmod, "HAS_HARDWARE", True):
                with patch.object(hmod, "adafruit_ahtx0", mock_ahtx0, create=True):
                    sensor = HumiditySensor()
                    assert sensor._sensor is not None

    def test_init_with_hardware_os_error(self):
        """Test hardware initialization when I2C raises OSError."""
        mock_busio = MagicMock()
        mock_busio.I2C.side_effect = OSError("No I2C device")
        mock_board = MagicMock()

        with patch.dict(
            "sys.modules",
            {"board": mock_board, "busio": mock_busio},
        ):
            with patch("src.hardware.sensors.humidity.HAS_HARDWARE", True):
                sensor = HumiditySensor()
                assert sensor._sensor is None


class TestHumiditySensorRead:
    def test_read_returns_humidity_value(self):
        sensor = HumiditySensor()
        sensor._sensor = MagicMock()
        sensor._sensor.relative_humidity = 65.0
        assert sensor.read() == 65.0

    def test_read_clamps_above_100(self):
        sensor = HumiditySensor()
        sensor._sensor = MagicMock()
        sensor._sensor.relative_humidity = 110.0
        assert sensor.read() == 100.0

    def test_read_clamps_below_0(self):
        sensor = HumiditySensor()
        sensor._sensor = MagicMock()
        sensor._sensor.relative_humidity = -5.0
        assert sensor.read() == 0.0

    def test_read_raises_on_io_error(self):
        sensor = HumiditySensor()
        sensor._sensor = MagicMock()
        sensor._sensor.relative_humidity = property(
            fget=MagicMock(side_effect=IOError("bus error"))
        )
        type(sensor._sensor).relative_humidity = property(
            fget=MagicMock(side_effect=IOError("bus error"))
        )
        with pytest.raises(SensorReadError):
            sensor.read()

    def test_read_raises_on_os_error(self):
        sensor = HumiditySensor()
        sensor._sensor = MagicMock()
        type(sensor._sensor).relative_humidity = property(
            fget=MagicMock(side_effect=OSError("device error"))
        )
        with pytest.raises(SensorReadError):
            sensor.read()

    def test_is_available_true_when_sensor_set(self):
        sensor = HumiditySensor()
        sensor._sensor = MagicMock()
        assert sensor.is_available() is True

    def test_is_available_false_when_no_sensor(self):
        sensor = HumiditySensor()
        assert sensor.is_available() is False


class TestTemperatureSensorInit:
    def test_init_with_hardware_success(self):
        mock_i2c = MagicMock()
        mock_sensor = MagicMock()
        mock_board = MagicMock()
        mock_busio = MagicMock()
        mock_busio.I2C.return_value = mock_i2c
        mock_ahtx0 = MagicMock()
        mock_ahtx0.AHTx0.return_value = mock_sensor

        with patch.dict(
            "sys.modules",
            {
                "board": mock_board,
                "busio": mock_busio,
                "adafruit_ahtx0": mock_ahtx0,
            },
        ):
            import src.hardware.sensors.temperature as tmod

            with patch.object(tmod, "HAS_HARDWARE", True):
                with patch.object(tmod, "adafruit_ahtx0", mock_ahtx0, create=True):
                    sensor = TemperatureSensor()
                    assert sensor._sensor is not None

    def test_init_with_hardware_os_error(self):
        mock_busio = MagicMock()
        mock_busio.I2C.side_effect = OSError("No I2C device")
        mock_board = MagicMock()

        with patch.dict(
            "sys.modules",
            {"board": mock_board, "busio": mock_busio},
        ):
            with patch("src.hardware.sensors.temperature.HAS_HARDWARE", True):
                sensor = TemperatureSensor()
                assert sensor._sensor is None


class TestTemperatureSensorRead:
    def test_read_raises_on_io_error(self):
        sensor = TemperatureSensor(unit="fahrenheit")
        sensor._sensor = MagicMock()
        type(sensor._sensor).temperature = property(
            fget=MagicMock(side_effect=IOError("bus error"))
        )
        with pytest.raises(SensorReadError):
            sensor.read()

    def test_read_raises_on_os_error(self):
        sensor = TemperatureSensor(unit="celsius")
        sensor._sensor = MagicMock()
        type(sensor._sensor).temperature = property(
            fget=MagicMock(side_effect=OSError("device error"))
        )
        with pytest.raises(SensorReadError):
            sensor.read()

    def test_read_raises_on_type_error(self):
        sensor = TemperatureSensor()
        sensor._sensor = MagicMock()
        type(sensor._sensor).temperature = property(
            fget=MagicMock(side_effect=TypeError("bad type"))
        )
        with pytest.raises(SensorReadError):
            sensor.read()

    def test_is_available_true(self):
        sensor = TemperatureSensor()
        sensor._sensor = MagicMock()
        assert sensor.is_available() is True


class TestCombinedSensorCoverage:
    def test_read_celsius_mode(self):
        sensor = CombinedSensor(unit="celsius")
        sensor._sensor = MagicMock()
        sensor._sensor.temperature = 25.0
        sensor._sensor.relative_humidity = 50.0
        result = sensor.read()
        assert result["temperature"] == 25.0
        assert result["humidity"] == 50.0

    def test_read_raises_on_io_error(self):
        sensor = CombinedSensor()
        sensor._sensor = MagicMock()
        type(sensor._sensor).temperature = property(
            fget=MagicMock(side_effect=IOError("bus error"))
        )
        with pytest.raises(SensorReadError):
            sensor.read()

    def test_read_raises_on_os_error(self):
        sensor = CombinedSensor()
        sensor._sensor = MagicMock()
        type(sensor._sensor).temperature = property(
            fget=MagicMock(side_effect=OSError("device error"))
        )
        with pytest.raises(SensorReadError):
            sensor.read()

    def test_read_clamps_humidity_above_100(self):
        sensor = CombinedSensor()
        sensor._sensor = MagicMock()
        sensor._sensor.temperature = 20.0
        sensor._sensor.relative_humidity = 110.0
        result = sensor.read()
        assert result["humidity"] == 100.0

    def test_is_available_true(self):
        sensor = CombinedSensor()
        sensor._sensor = MagicMock()
        assert sensor.is_available() is True
