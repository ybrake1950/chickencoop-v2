"""Coverage improvement tests for remaining low-coverage modules.

Covers:
- src/utils/process.py (75% -> 80%+)
- src/api/routes/sensors.py (78% -> 80%+)
- src/security/validation.py (79% -> 80%+)
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.utils.process import run_command
from src.security.validation import (
    SQLInjectionDetector,
    PathTraversalDetector,
    CommandInjectionDetector,
    InputValidator,
)


class TestRunCommandCoverage:
    def test_run_command_returns_completed_process(self):
        result = run_command(["echo", "hello"])
        assert isinstance(result, subprocess.CompletedProcess)

    def test_run_command_captures_stdout(self):
        result = run_command(["echo", "hello"])
        assert "hello" in result.stdout

    def test_run_command_with_custom_timeout(self):
        result = run_command(["echo", "test"], timeout=5)
        assert result.returncode == 0


class TestSQLInjectionDetectorCoverage:
    def test_clean_input_not_suspicious(self):
        detector = SQLInjectionDetector()
        assert detector.is_suspicious("hello world") is False

    def test_check_valid_returns_valid_result(self):
        detector = SQLInjectionDetector()
        result = detector.check("normal text")
        assert result.valid is True

    def test_check_suspicious_returns_invalid(self):
        detector = SQLInjectionDetector()
        result = detector.check("'; DROP TABLE users; --")
        assert result.valid is False


class TestPathTraversalDetectorCoverage:
    def test_clean_path_not_suspicious(self):
        detector = PathTraversalDetector()
        assert detector.is_suspicious("videos/file.mp4") is False

    def test_check_valid_returns_valid_result(self):
        detector = PathTraversalDetector()
        result = detector.check("videos/file.mp4")
        assert result.valid is True

    def test_check_suspicious_returns_invalid(self):
        detector = PathTraversalDetector()
        result = detector.check("../../../etc/passwd")
        assert result.valid is False


class TestCommandInjectionDetectorCoverage:
    def test_clean_input_not_suspicious(self):
        detector = CommandInjectionDetector()
        assert detector.is_suspicious("hello") is False

    def test_check_valid_returns_valid_result(self):
        detector = CommandInjectionDetector()
        result = detector.check("normal text")
        assert result.valid is True

    def test_check_suspicious_returns_invalid(self):
        detector = CommandInjectionDetector()
        result = detector.check("foo; rm -rf /")
        assert result.valid is False


class TestSensorRoutesCoverage:
    """Test the sensor routes for unauthenticated access."""

    def test_download_csv_unauthenticated_returns_401(self):
        """Importing Flask routes and testing requires a Flask app context.
        This test verifies the route registration works correctly.
        """
        from flask import Flask
        from src.api.routes.sensors import register_routes

        app = Flask(__name__)
        app.secret_key = "test-secret"
        register_routes(app)

        with app.test_client() as client:
            response = client.get("/api/download-csv")
            assert response.status_code == 401

    def test_sensor_data_returns_200(self):
        from flask import Flask
        from src.api.routes.sensors import register_routes

        app = Flask(__name__)
        app.secret_key = "test-secret"
        register_routes(app)

        with app.test_client() as client:
            response = client.get("/api/sensor-data")
            assert response.status_code == 200
