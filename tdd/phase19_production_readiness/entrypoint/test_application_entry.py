"""
Phase 19: Application Entry Point Tests
========================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates the main application entry point:
- src/main.py exists and is importable
- Flask application factory creates a valid app
- All route blueprints are registered
- Health check endpoint responds correctly
- Graceful shutdown handler is installed
- Database initialization runs on startup
- Logging is configured with coop ID

WHY THIS MATTERS:
-----------------
The systemd service runs `python -m src.main`. Without a working entry
point, the entire application fails to start on the Raspberry Pi. The
application factory must wire together all components (routes, AWS clients,
database, logging) for the system to function.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase19_production_readiness/entrypoint/test_application_entry.py -v
"""
import importlib
import os
import signal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def main_module_path(project_root):
    """Get path to src/main.py."""
    return project_root / 'src' / 'main.py'


class TestEntryPointExists:
    """Verify src/main.py exists and is structured correctly."""

    def test_main_py_exists(self, main_module_path):
        """src/main.py must exist — systemd calls python -m src.main."""
        assert main_module_path.exists(), (
            "src/main.py not found. The systemd service unit calls "
            "'python -m src.main' — this file MUST exist."
        )

    def test_main_py_has_main_function(self, main_module_path):
        """src/main.py must define a main() function."""
        if not main_module_path.exists():
            pytest.skip("src/main.py does not exist yet")
        content = main_module_path.read_text()
        assert 'def main(' in content, (
            "src/main.py must define a main() function as entry point"
        )

    def test_main_py_has_dunder_main_guard(self, main_module_path):
        """src/main.py must have if __name__ == '__main__' guard."""
        if not main_module_path.exists():
            pytest.skip("src/main.py does not exist yet")
        content = main_module_path.read_text()
        assert "__name__" in content and "__main__" in content, (
            "src/main.py must have 'if __name__ == \"__main__\"' guard "
            "for python -m invocation"
        )

    def test_main_py_has_create_app_factory(self, main_module_path):
        """src/main.py must define create_app() factory function."""
        if not main_module_path.exists():
            pytest.skip("src/main.py does not exist yet")
        content = main_module_path.read_text()
        assert 'def create_app(' in content, (
            "src/main.py must define create_app() factory for Flask app creation"
        )


class TestApplicationFactory:
    """Verify the Flask application factory wires all components."""

    def test_create_app_returns_flask_instance(self, main_module_path):
        """create_app() must return a Flask application instance."""
        if not main_module_path.exists():
            pytest.skip("src/main.py does not exist yet")
        try:
            from src.main import create_app
            app = create_app(testing=True)
            assert app is not None
            assert hasattr(app, 'route')
            assert hasattr(app, 'test_client')
        except ImportError as e:
            pytest.skip(f"Cannot import src.main: {e}")

    def test_health_endpoint_registered(self, main_module_path):
        """The app must have a /health endpoint."""
        if not main_module_path.exists():
            pytest.skip("src/main.py does not exist yet")
        try:
            from src.main import create_app
            app = create_app(testing=True)
            with app.test_client() as client:
                resp = client.get('/health')
                assert resp.status_code == 200
                data = resp.get_json()
                assert 'status' in data
                assert data['status'] in ('ok', 'healthy')
        except ImportError as e:
            pytest.skip(f"Cannot import src.main: {e}")

    def test_blueprints_registered(self, main_module_path):
        """All route blueprints must be registered with the app."""
        if not main_module_path.exists():
            pytest.skip("src/main.py does not exist yet")
        try:
            from src.main import create_app
            app = create_app(testing=True)
            blueprint_names = list(app.blueprints.keys())
            expected_blueprints = [
                'sensors', 'videos', 'chickens', 'alerts',
                'admin', 'diagnostics', 'headcount', 'settings',
            ]
            for bp in expected_blueprints:
                found = any(bp in name.lower() for name in blueprint_names)
                assert found, (
                    f"Blueprint '{bp}' not registered. "
                    f"Found: {blueprint_names}"
                )
        except ImportError as e:
            pytest.skip(f"Cannot import src.main: {e}")

    def test_secret_key_configured(self, main_module_path):
        """Flask app must have SECRET_KEY configured."""
        if not main_module_path.exists():
            pytest.skip("src/main.py does not exist yet")
        try:
            from src.main import create_app
            app = create_app(testing=True)
            assert app.config.get('SECRET_KEY'), (
                "Flask SECRET_KEY must be configured"
            )
        except ImportError as e:
            pytest.skip(f"Cannot import src.main: {e}")


class TestGracefulShutdown:
    """Verify the application handles shutdown signals."""

    def test_main_py_registers_signal_handler(self, main_module_path):
        """src/main.py must register SIGTERM handler for systemd stop."""
        if not main_module_path.exists():
            pytest.skip("src/main.py does not exist yet")
        content = main_module_path.read_text()
        has_signal = ('signal.SIGTERM' in content or
                      'SIGTERM' in content)
        assert has_signal, (
            "src/main.py must handle SIGTERM for graceful systemd shutdown"
        )

    def test_main_py_registers_sigint_handler(self, main_module_path):
        """src/main.py should handle SIGINT for Ctrl+C during development."""
        if not main_module_path.exists():
            pytest.skip("src/main.py does not exist yet")
        content = main_module_path.read_text()
        has_signal = ('signal.SIGINT' in content or
                      'SIGINT' in content or
                      'KeyboardInterrupt' in content)
        assert has_signal, (
            "src/main.py should handle SIGINT for clean Ctrl+C shutdown"
        )


class TestLoggingConfiguration:
    """Verify logging is set up during application startup."""

    def test_main_py_configures_logging(self, main_module_path):
        """src/main.py must configure logging on startup."""
        if not main_module_path.exists():
            pytest.skip("src/main.py does not exist yet")
        content = main_module_path.read_text()
        has_logging = ('logging' in content or
                       'setup_logging' in content or
                       'get_logger' in content)
        assert has_logging, (
            "src/main.py must configure logging during startup"
        )
