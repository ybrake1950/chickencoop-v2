"""
Phase 11: Interface Contracts Tests
===================================

FUNCTIONALITY BEING TESTED:
---------------------------
- Abstract base classes for sensors/cameras
- Interface segregation
- Contract enforcement
- Type hints and documentation

WHY THIS MATTERS:
-----------------
Well-defined interfaces enable loose coupling, easier testing with mocks,
and the ability to swap implementations. They also serve as documentation
for expected behavior.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase11_code_quality/interfaces/test_interface_contracts.py -v
"""
import pytest
from abc import ABC, abstractmethod
import inspect
from unittest.mock import MagicMock


# =============================================================================
# TestSensorInterface
# =============================================================================

class TestSensorInterface:
    """Test sensor interface definition."""

    def test_sensor_interface_exists(self):
        """BaseSensor interface is defined."""
        from src.hardware.sensors.base import BaseSensor

        # Should be an abstract base class
        assert inspect.isclass(BaseSensor)
        assert issubclass(BaseSensor, ABC) or hasattr(BaseSensor, '__abstractmethods__')

    def test_sensor_has_read_method(self):
        """Sensor interface requires read() method."""
        from src.hardware.sensors.base import BaseSensor

        # read() should be abstract
        assert hasattr(BaseSensor, 'read')
        assert 'read' in BaseSensor.__abstractmethods__ or callable(getattr(BaseSensor, 'read', None))

    def test_sensor_has_name_property(self):
        """Sensor interface has name property."""
        from src.hardware.sensors.base import BaseSensor

        assert hasattr(BaseSensor, 'name')

    def test_all_sensors_implement_interface(self):
        """All sensor classes implement BaseSensor."""
        from src.hardware.sensors.base import BaseSensor
        from src.hardware.sensors.temperature import TemperatureSensor
        from src.hardware.sensors.humidity import HumiditySensor
        from src.hardware.sensors.combined import CombinedSensor

        sensors = [TemperatureSensor, HumiditySensor, CombinedSensor]

        for sensor_class in sensors:
            assert issubclass(sensor_class, BaseSensor), f"{sensor_class} doesn't implement BaseSensor"


# =============================================================================
# TestCameraInterface
# =============================================================================

class TestCameraInterface:
    """Test camera interface definition."""

    def test_camera_interface_exists(self):
        """BaseCamera interface is defined."""
        from src.hardware.camera.base import BaseCamera

        assert inspect.isclass(BaseCamera)
        assert issubclass(BaseCamera, ABC) or hasattr(BaseCamera, '__abstractmethods__')

    def test_camera_has_capture_method(self):
        """Camera interface requires capture() method."""
        from src.hardware.camera.base import BaseCamera

        assert hasattr(BaseCamera, 'capture')

    def test_camera_has_record_method(self):
        """Camera interface requires record() method."""
        from src.hardware.camera.base import BaseCamera

        assert hasattr(BaseCamera, 'record')

    def test_camera_has_status_property(self):
        """Camera interface has status property."""
        from src.hardware.camera.base import BaseCamera

        assert hasattr(BaseCamera, 'status') or hasattr(BaseCamera, 'get_status')


# =============================================================================
# TestStorageInterface
# =============================================================================

class TestStorageInterface:
    """Test storage interface definition."""

    def test_storage_interface_exists(self):
        """BaseStorage interface is defined."""
        from src.persistence.base import BaseStorage

        assert inspect.isclass(BaseStorage)

    def test_storage_has_save_method(self):
        """Storage interface requires save() method."""
        from src.persistence.base import BaseStorage

        assert hasattr(BaseStorage, 'save')

    def test_storage_has_load_method(self):
        """Storage interface requires load() method."""
        from src.persistence.base import BaseStorage

        assert hasattr(BaseStorage, 'load') or hasattr(BaseStorage, 'get')

    def test_csv_storage_implements_interface(self):
        """CSVStorage implements BaseStorage."""
        from src.persistence.base import BaseStorage
        from src.persistence.csv_storage import CSVStorage

        assert issubclass(CSVStorage, BaseStorage)


# =============================================================================
# TestAWSClientInterfaces
# =============================================================================

class TestAWSClientInterfaces:
    """Test AWS client interfaces."""

    def test_s3_client_interface(self):
        """S3Client has expected methods."""
        from src.aws.s3.client import S3Client

        expected_methods = ['upload_file', 'download_file', 'generate_presigned_url']

        for method in expected_methods:
            assert hasattr(S3Client, method), f"S3Client missing {method}"

    def test_iot_client_interface(self):
        """IoTClient has expected methods."""
        from src.aws.iot.client import IoTClient

        expected_methods = ['publish', 'subscribe']

        for method in expected_methods:
            assert hasattr(IoTClient, method), f"IoTClient missing {method}"

    def test_sns_client_interface(self):
        """SNSClient has expected methods."""
        from src.aws.sns.client import SNSClient

        expected_methods = ['publish', 'subscribe']

        for method in expected_methods:
            assert hasattr(SNSClient, method), f"SNSClient missing {method}"


# =============================================================================
# TestInterfaceSegregation
# =============================================================================

class TestInterfaceSegregation:
    """Test interface segregation principle."""

    def test_reader_writer_separation(self):
        """Read and write operations can be separated."""
        # Check that interfaces aren't bloated
        from src.persistence.repositories.sensor import SensorRepository

        # Repository should have focused methods
        methods = [m for m in dir(SensorRepository) if not m.startswith('_')]

        # Shouldn't have unrelated methods
        assert 'send_email' not in methods
        assert 'render_html' not in methods

    def test_sensor_interface_focused(self):
        """Sensor interface only has sensor concerns."""
        from src.hardware.sensors.base import BaseSensor

        methods = [m for m in dir(BaseSensor) if not m.startswith('_')]

        # Should be focused on sensing
        assert 'upload_to_s3' not in methods
        assert 'send_alert' not in methods


# =============================================================================
# TestTypeHints
# =============================================================================

class TestTypeHints:
    """Test type hints and documentation."""

    def test_public_methods_have_type_hints(self):
        """Public methods have type hints."""
        from src.services.sensor_service import SensorService

        sig = inspect.signature(SensorService.process_reading)
        params = sig.parameters

        # Should have some type annotations
        has_annotations = any(
            p.annotation != inspect.Parameter.empty
            for p in params.values()
            if p.name != 'self'
        )

        assert has_annotations or sig.return_annotation != inspect.Signature.empty

    def test_data_classes_have_type_hints(self):
        """Data classes/models have type hints."""
        from src.models.sensor import SensorReading

        # Should have type annotations
        annotations = getattr(SensorReading, '__annotations__', {})
        assert len(annotations) > 0

    def test_interfaces_documented(self):
        """Interface classes have docstrings."""
        from src.hardware.sensors.base import BaseSensor

        assert BaseSensor.__doc__ is not None
        assert len(BaseSensor.__doc__) > 10


# =============================================================================
# TestContractEnforcement
# =============================================================================

class TestContractEnforcement:
    """Test that contracts are enforced."""

    def test_cannot_instantiate_abstract(self):
        """Cannot instantiate abstract base class."""
        from src.hardware.sensors.base import BaseSensor

        with pytest.raises(TypeError):
            BaseSensor()

    def test_incomplete_implementation_fails(self):
        """Incomplete implementation raises TypeError."""
        from src.hardware.sensors.base import BaseSensor

        class IncompleteSensor(BaseSensor):
            pass  # Missing required methods

        with pytest.raises(TypeError):
            IncompleteSensor()

    def test_return_type_consistency(self):
        """Implementations return expected types."""
        from src.hardware.sensors.combined import CombinedSensor

        sensor = CombinedSensor()
        reading = sensor.read()

        # Should return dict with expected keys
        assert isinstance(reading, dict)
        assert 'temperature' in reading or 'humidity' in reading
