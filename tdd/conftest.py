"""
Shared pytest fixtures for TDD test suite.

This module provides common fixtures used across all test phases.
Fixtures are organized by category and build upon each other.
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# Path and Environment Fixtures
# =============================================================================

@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def temp_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary file path."""
    file_path = tmp_path / "temp_file.txt"
    yield file_path
    if file_path.exists():
        file_path.unlink()


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Provide a clean environment without project-specific variables."""
    env_vars_to_clear = [
        'COOP_ID', 'SECRET_KEY', 'TESTING', 'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 'AWS_REGION'
    ]
    original_values = {k: os.environ.get(k) for k in env_vars_to_clear}

    for var in env_vars_to_clear:
        if var in os.environ:
            del os.environ[var]

    yield

    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]


@pytest.fixture
def test_env() -> Generator[None, None, None]:
    """Set up test environment variables."""
    os.environ['TESTING'] = 'true'
    os.environ['COOP_ID'] = 'test'
    os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
    yield
    del os.environ['TESTING']
    del os.environ['COOP_ID']
    del os.environ['SECRET_KEY']


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Provide a valid application configuration."""
    return {
        "sensors": {
            "read_interval": 300,
            "temperature": {
                "min_threshold": 32,
                "max_threshold": 95,
                "unit": "fahrenheit"
            },
            "humidity": {
                "min_threshold": 30,
                "max_threshold": 80
            }
        },
        "camera": {
            "resolution": [1280, 720],
            "framerate": 24,
            "rotation": 0
        },
        "motion": {
            "enabled": True,
            "sensitivity": 50,
            "min_area": 500,
            "recording_duration": 30
        },
        "headcount": {
            "enabled": True,
            "schedule_time": "19:00",
            "expected_count": 6
        }
    }


@pytest.fixture
def sample_aws_config() -> Dict[str, Any]:
    """Provide a valid AWS configuration."""
    return {
        "region": "us-east-1",
        "s3": {
            "bucket": "test-chickencoop-bucket",
            "video_prefix": "videos/",
            "csv_prefix": "csv/"
        },
        "iot": {
            "endpoint": "test-iot.iot.us-east-1.amazonaws.com",
            "thing_name": "test-coop",
            "topic_prefix": "chickencoop/test"
        },
        "sns": {
            "topic_arn": "arn:aws:sns:us-east-1:123456789:test-alerts"
        }
    }


@pytest.fixture
def sample_device_config() -> Dict[str, Any]:
    """Provide a valid device-specific configuration."""
    return {
        "device_id": "test-coop",
        "device_type": "raspberry_pi_4",
        "camera": {
            "resolution": [1920, 1080],
            "framerate": 30
        },
        "sensors": {
            "i2c_bus": 1
        }
    }


@pytest.fixture
def config_file(tmp_path: Path, sample_config: Dict[str, Any]) -> Path:
    """Create a temporary config file."""
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(sample_config, indent=2))
    return config_path


@pytest.fixture
def aws_config_file(tmp_path: Path, sample_aws_config: Dict[str, Any]) -> Path:
    """Create a temporary AWS config file."""
    config_path = tmp_path / "aws_config.json"
    config_path.write_text(json.dumps(sample_aws_config, indent=2))
    return config_path


# =============================================================================
# Model Fixtures
# =============================================================================

@pytest.fixture
def sample_sensor_reading() -> Dict[str, Any]:
    """Provide a sample sensor reading."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature": 72.5,
        "humidity": 65.0,
        "coop_id": "test"
    }


@pytest.fixture
def sample_video_metadata() -> Dict[str, Any]:
    """Provide sample video metadata."""
    return {
        "filename": "motion_20250125_143000.mp4",
        "s3_key": "videos/test/motion_20250125_143000.mp4",
        "camera": "indoor",
        "duration": 30,
        "size_bytes": 15000000,
        "upload_date": datetime.now(timezone.utc).isoformat(),
        "retain_permanently": False
    }


@pytest.fixture
def sample_chicken() -> Dict[str, Any]:
    """Provide sample chicken data."""
    return {
        "name": "Henrietta",
        "breed": "Rhode Island Red",
        "color": "red",
        "date_registered": datetime.now(timezone.utc).isoformat(),
        "is_active": True,
        "notes": "Friendly, easy to identify"
    }


@pytest.fixture
def sample_headcount_log() -> Dict[str, Any]:
    """Provide sample headcount log data."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "count_detected": 5,
        "expected_count": 6,
        "all_present": False,
        "confidence": 0.85,
        "method": "simple_count"
    }


@pytest.fixture
def sample_user() -> Dict[str, Any]:
    """Provide sample user data."""
    return {
        "email": "test@example.com",
        "password": "secure_password_123",
        "is_active": True
    }


# =============================================================================
# Hardware Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_i2c_bus() -> MagicMock:
    """Provide a mocked I2C bus."""
    mock_bus = MagicMock()
    mock_bus.read_byte_data.return_value = 0
    mock_bus.read_i2c_block_data.return_value = [0] * 8
    return mock_bus


@pytest.fixture
def mock_temperature_sensor(mock_i2c_bus: MagicMock) -> MagicMock:
    """Provide a mocked temperature sensor."""
    sensor = MagicMock()
    sensor.temperature = 72.5
    sensor.relative_humidity = 65.0
    return sensor


@pytest.fixture
def mock_camera() -> MagicMock:
    """Provide a mocked Picamera2 instance."""
    camera = MagicMock()
    camera.started = False
    camera.capture_array.return_value = MagicMock()  # numpy array mock
    camera.start.side_effect = lambda: setattr(camera, 'started', True)
    camera.stop.side_effect = lambda: setattr(camera, 'started', False)
    return camera


@pytest.fixture
def mock_video_frame() -> MagicMock:
    """Provide a mocked video frame (numpy array)."""
    import numpy as np
    # 720p frame with 3 color channels
    return np.zeros((720, 1280, 3), dtype=np.uint8)


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture
def in_memory_db() -> Generator[Any, None, None]:
    """Provide an in-memory SQLite database."""
    import sqlite3
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Provide a path for a test database file."""
    return tmp_path / "test_chickencoop.db"


# =============================================================================
# AWS Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_s3_client() -> MagicMock:
    """Provide a mocked S3 client."""
    client = MagicMock()
    client.upload_file.return_value = None
    client.download_file.return_value = None
    client.generate_presigned_url.return_value = "https://example.com/presigned"
    client.list_objects_v2.return_value = {"Contents": []}
    return client


@pytest.fixture
def mock_iot_client() -> MagicMock:
    """Provide a mocked IoT Data client."""
    client = MagicMock()
    client.publish.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    return client


@pytest.fixture
def mock_sns_client() -> MagicMock:
    """Provide a mocked SNS client."""
    client = MagicMock()
    client.publish.return_value = {"MessageId": "test-message-id"}
    client.subscribe.return_value = {"SubscriptionArn": "pending confirmation"}
    return client


@pytest.fixture
def mock_boto3_session() -> Generator[MagicMock, None, None]:
    """Provide a mocked boto3 session."""
    with patch('boto3.Session') as mock_session:
        yield mock_session


# =============================================================================
# Time Fixtures
# =============================================================================

@pytest.fixture
def fixed_datetime() -> datetime:
    """Provide a fixed datetime for consistent testing."""
    return datetime(2025, 1, 25, 14, 30, 0, tzinfo=timezone.utc)


@pytest.fixture
def freeze_time(fixed_datetime: datetime) -> Generator[None, None, None]:
    """Freeze time to a fixed datetime."""
    try:
        from freezegun import freeze_time as ft
        with ft(fixed_datetime):
            yield
    except ImportError:
        # If freezegun not installed, just yield
        yield


# =============================================================================
# Flask Test Fixtures
# =============================================================================

@pytest.fixture
def flask_app() -> Generator[Any, None, None]:
    """Provide a Flask test application."""
    try:
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['WTF_CSRF_ENABLED'] = False
        yield app
    except ImportError:
        yield None


@pytest.fixture
def flask_client(flask_app: Any) -> Generator[Any, None, None]:
    """Provide a Flask test client."""
    if flask_app:
        with flask_app.test_client() as client:
            yield client
    else:
        yield None


# =============================================================================
# File Content Fixtures
# =============================================================================

@pytest.fixture
def sample_csv_content() -> str:
    """Provide sample CSV content."""
    return """timestamp,temperature,humidity,coop_id
2025-01-25 14:00:00,72.5,65.0,test
2025-01-25 14:05:00,72.8,64.5,test
2025-01-25 14:10:00,73.0,64.0,test
"""


@pytest.fixture
def csv_file(tmp_path: Path, sample_csv_content: str) -> Path:
    """Create a temporary CSV file with sample data."""
    csv_path = tmp_path / "sensor_data.csv"
    csv_path.write_text(sample_csv_content)
    return csv_path


# =============================================================================
# Utility Functions
# =============================================================================

def create_test_image(width: int = 1280, height: int = 720) -> Any:
    """Create a test image array."""
    try:
        import numpy as np
        return np.zeros((height, width, 3), dtype=np.uint8)
    except ImportError:
        return None


def create_test_video_file(path: Path, duration: int = 1) -> Path:
    """Create a minimal test video file."""
    # Create a minimal MP4 file header
    path.write_bytes(b'\x00\x00\x00\x1c\x66\x74\x79\x70\x69\x73\x6f\x6d')
    return path
