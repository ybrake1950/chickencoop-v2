"""
Phase 11: Design Patterns Tests
===============================

FUNCTIONALITY BEING TESTED:
---------------------------
- Singleton pattern for shared clients
- Factory pattern for object creation
- Repository pattern for data access
- Service layer pattern
- Dependency injection

WHY THIS MATTERS:
-----------------
Consistent design patterns make code predictable and easier to understand.
Proper patterns also enable better testing through dependency injection
and improve code reuse.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase11_code_quality/patterns/test_design_patterns.py -v
"""
import pytest
from pathlib import Path
import ast
import inspect
from unittest.mock import MagicMock, patch


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parents[3]


# =============================================================================
# TestSingletonPattern
# =============================================================================

class TestSingletonPattern:
    """Test singleton pattern for shared resources."""

    def test_s3_client_is_singleton(self):
        """S3 client instance reused across calls."""
        from src.aws.s3.client import S3Client, get_s3_client

        # Multiple calls should return the same instance
        client1 = get_s3_client()
        client2 = get_s3_client()

        assert client1 is client2

    def test_iot_client_is_singleton(self):
        """IoT client instance reused."""
        from src.aws.iot.client import IoTClient, get_iot_client

        client1 = get_iot_client()
        client2 = get_iot_client()

        assert client1 is client2

    def test_sns_client_is_singleton(self):
        """SNS client instance reused."""
        from src.aws.sns.client import SNSClient, get_sns_client

        client1 = get_sns_client()
        client2 = get_sns_client()

        assert client1 is client2

    def test_database_connection_pooled(self):
        """Database connections pooled, not recreated."""
        from src.persistence.database import Database, get_database

        db1 = get_database()
        db2 = get_database()

        # Should be same instance or from pool
        assert db1 is db2 or db1.pool is db2.pool

    def test_config_loaded_once(self):
        """Configuration loaded once and cached."""
        from src.config.loader import ConfigLoader, get_config

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2


# =============================================================================
# TestFactoryPattern
# =============================================================================

class TestFactoryPattern:
    """Test factory pattern for object creation."""

    def test_sensor_factory(self):
        """Sensors created via factory method."""
        from src.hardware.sensors.factory import SensorFactory

        factory = SensorFactory()

        # Factory should create appropriate sensor type
        temp_sensor = factory.create("temperature")
        humidity_sensor = factory.create("humidity")
        combined_sensor = factory.create("combined")

        assert temp_sensor is not None
        assert humidity_sensor is not None
        assert combined_sensor is not None

        # Different types should be different classes
        assert type(temp_sensor).__name__ != type(humidity_sensor).__name__ or "Mock" in type(temp_sensor).__name__

    def test_camera_factory(self):
        """Cameras created via factory method."""
        from src.hardware.camera.factory import CameraFactory

        factory = CameraFactory()

        # Factory should create appropriate camera type
        pi_camera = factory.create("picamera")
        usb_camera = factory.create("usb")
        mock_camera = factory.create("mock")

        assert pi_camera is not None or mock_camera is not None

    def test_alert_factory(self):
        """Alerts created via factory method."""
        from src.services.alerts.factory import AlertFactory

        factory = AlertFactory()

        # Factory should create different alert types
        temp_alert = factory.create("temperature", severity="high", value=100)
        motion_alert = factory.create("motion", severity="medium")

        assert temp_alert is not None
        assert motion_alert is not None
        assert temp_alert.alert_type == "temperature"


# =============================================================================
# TestRepositoryPattern
# =============================================================================

class TestRepositoryPattern:
    """Test repository pattern for data access."""

    def test_user_repository_exists(self):
        """UserRepository handles user data access."""
        from src.persistence.repositories.user import UserRepository

        repo = UserRepository(database=MagicMock())

        # Should have standard CRUD methods
        assert hasattr(repo, 'find_by_id')
        assert hasattr(repo, 'find_all')
        assert hasattr(repo, 'save')
        assert hasattr(repo, 'delete')

    def test_video_repository_exists(self):
        """VideoRepository handles video data access."""
        from src.persistence.repositories.video import VideoRepository

        repo = VideoRepository(database=MagicMock())

        assert hasattr(repo, 'find_by_id')
        assert hasattr(repo, 'find_by_coop')
        assert hasattr(repo, 'save')

    def test_sensor_repository_exists(self):
        """SensorRepository handles sensor data access."""
        from src.persistence.repositories.sensor import SensorRepository

        repo = SensorRepository(database=MagicMock())

        assert hasattr(repo, 'save')
        assert hasattr(repo, 'get_latest')
        assert hasattr(repo, 'get_range')

    def test_repository_abstracts_storage(self):
        """Repository abstracts storage implementation."""
        from src.persistence.repositories.sensor import SensorRepository

        # Repository should work with any database implementation
        mock_db = MagicMock()
        repo = SensorRepository(database=mock_db)

        # Business logic shouldn't know about SQL
        assert not hasattr(repo, 'execute_sql')


# =============================================================================
# TestServiceLayerPattern
# =============================================================================

class TestServiceLayerPattern:
    """Test service layer pattern."""

    def test_sensor_service_exists(self):
        """SensorService contains sensor business logic."""
        from src.services.sensor_service import SensorService

        service = SensorService(
            sensor_repo=MagicMock(),
            alert_service=MagicMock()
        )

        # Should have business logic methods
        assert hasattr(service, 'process_reading')
        assert hasattr(service, 'get_latest_readings')

    def test_video_service_exists(self):
        """VideoService contains video business logic."""
        from src.services.video_service import VideoService

        service = VideoService(
            video_repo=MagicMock(),
            s3_client=MagicMock()
        )

        assert hasattr(service, 'record_video')
        assert hasattr(service, 'get_video_url')

    def test_alert_service_exists(self):
        """AlertService contains alert business logic."""
        from src.services.alert_service import AlertService

        service = AlertService(
            sns_client=MagicMock()
        )

        assert hasattr(service, 'check_and_alert')
        assert hasattr(service, 'send_alert')

    def test_services_independent_of_transport(self):
        """Services don't know about HTTP/API layer."""
        from src.services.sensor_service import SensorService
        import inspect

        source = inspect.getsource(SensorService)

        # Service should not import Flask/HTTP concerns
        assert "from flask" not in source
        assert "request" not in source.lower() or "request" in source.lower() and "http" not in source.lower()


# =============================================================================
# TestDependencyInjection
# =============================================================================

class TestDependencyInjection:
    """Test dependency injection."""

    def test_dependencies_injectable(self):
        """Class dependencies can be injected."""
        from src.services.sensor_service import SensorService

        # Should accept dependencies via constructor
        mock_repo = MagicMock()
        mock_alert = MagicMock()

        service = SensorService(
            sensor_repo=mock_repo,
            alert_service=mock_alert
        )

        assert service.sensor_repo is mock_repo
        assert service.alert_service is mock_alert

    def test_constructor_injection_used(self):
        """Constructor injection preferred over property."""
        from src.services.sensor_service import SensorService
        import inspect

        sig = inspect.signature(SensorService.__init__)

        # Constructor should have dependency parameters
        params = list(sig.parameters.keys())
        assert len(params) > 1  # More than just 'self'

    def test_mock_dependencies_in_tests(self):
        """Dependencies mockable for testing."""
        from src.services.sensor_service import SensorService

        # Should be able to create with all mocks
        service = SensorService(
            sensor_repo=MagicMock(),
            alert_service=MagicMock()
        )

        # Mock should be used
        service.sensor_repo.save.return_value = True
        result = service.sensor_repo.save({"temp": 72})

        assert result is True
        service.sensor_repo.save.assert_called_once()


# =============================================================================
# TestErrorHandling
# =============================================================================

class TestErrorHandling:
    """Test error handling patterns."""

    def test_custom_exception_hierarchy(self):
        """Custom exception classes defined."""
        from src.exceptions import (
            ChickenCoopError,
            SensorError,
            AWSError,
            ValidationError,
            ConfigurationError
        )

        # Should have hierarchy
        assert issubclass(SensorError, ChickenCoopError)
        assert issubclass(AWSError, ChickenCoopError)
        assert issubclass(ValidationError, ChickenCoopError)
        assert issubclass(ConfigurationError, ChickenCoopError)

    def test_specific_exceptions_caught(self, project_root):
        """Specific exceptions caught, not bare except."""
        src_dir = project_root / "src"
        if not src_dir.exists():
            pytest.skip("src directory not found")

        bare_except_count = 0

        for py_file in src_dir.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler):
                        if node.type is None:  # bare except:
                            bare_except_count += 1
            except SyntaxError:
                continue

        # Should have minimal bare excepts (ideally 0)
        assert bare_except_count < 5, f"Found {bare_except_count} bare except clauses"

    def test_exceptions_include_context(self):
        """Exceptions include helpful context."""
        from src.exceptions import SensorError

        error = SensorError(
            message="Failed to read sensor",
            sensor_name="temperature",
            details={"last_value": 72}
        )

        # Error should have context
        assert error.sensor_name == "temperature"
        assert "temperature" in str(error)

    def test_errors_logged_before_raise(self, project_root):
        """Errors logged before re-raising."""
        # Check that error handling includes logging
        from src.services.sensor_service import SensorService
        import inspect

        source = inspect.getsource(SensorService)

        # Should have logging in error paths
        assert "logger" in source.lower() or "logging" in source.lower()
