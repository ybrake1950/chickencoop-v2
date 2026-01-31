"""
Phase 21: Systemd Service Production Configuration Tests
=========================================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates the systemd service file is production-ready:
- WorkingDirectory points to correct path (chickencoop-v2)
- Environment=COOP_ID is set for hostname-based detection
- EnvironmentFile loads .env for secrets
- StandardOutput/StandardError configured for logging
- ExecStartPre runs cleanup tasks
- Restart policy and timing are correct

WHY THIS MATTERS:
-----------------
The systemd service is the ONLY mechanism that keeps the monitoring
daemon running on each Raspberry Pi. Wrong paths, missing environment
variables, or absent logging directives cause silent failures that
are difficult to debug in the field.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase21_configuration/service_config/test_systemd_production.py -v
"""
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def service_file_path(project_root):
    """Get path to the systemd service file."""
    return project_root / 'config' / 'systemd' / 'chickencoop-monitor.service'


@pytest.fixture
def service_content(service_file_path):
    """Load service file content."""
    if service_file_path.exists():
        return service_file_path.read_text()
    return None


class TestServiceFilePaths:
    """Verify service file uses correct paths."""

    def test_service_file_exists(self, service_file_path):
        """Systemd service file must exist."""
        assert service_file_path.exists(), (
            "config/systemd/chickencoop-monitor.service not found"
        )

    def test_working_directory_is_v2(self, service_content):
        """WorkingDirectory must reference chickencoop-v2."""
        if service_content is None:
            pytest.skip("Service file does not exist yet")
        assert 'chickencoop-v2' in service_content or 'chickencoop' in service_content, (
            "WorkingDirectory should reference the project directory"
        )
        # Specifically check it's not the old path without -v2
        if 'WorkingDirectory' in service_content:
            for line in service_content.splitlines():
                if line.strip().startswith('WorkingDirectory='):
                    path = line.split('=', 1)[1].strip()
                    if 'chickencoop' in path and 'chickencoop-v2' not in path:
                        pytest.fail(
                            f"WorkingDirectory={path} uses old path. "
                            "Should be /home/pi/chickencoop-v2"
                        )


class TestServiceEnvironment:
    """Verify environment configuration in service file."""

    def test_coop_id_environment_set(self, service_content):
        """Service must set COOP_ID environment variable."""
        if service_content is None:
            pytest.skip("Service file does not exist yet")
        assert 'COOP_ID' in service_content, (
            "Service file must set Environment=COOP_ID for "
            "hostname-based coop detection"
        )

    def test_environment_file_directive(self, service_content):
        """Service should load .env file via EnvironmentFile."""
        if service_content is None:
            pytest.skip("Service file does not exist yet")
        assert 'EnvironmentFile' in service_content, (
            "Service file should use EnvironmentFile= to load "
            ".env secrets file"
        )


class TestServiceLogging:
    """Verify logging configuration in service file."""

    def test_stdout_logging_configured(self, service_content):
        """StandardOutput must direct logs to file or journal."""
        if service_content is None:
            pytest.skip("Service file does not exist yet")
        has_stdout = ('StandardOutput' in service_content or
                      'journal' in service_content.lower())
        assert has_stdout, (
            "Service must configure StandardOutput for log capture"
        )

    def test_stderr_logging_configured(self, service_content):
        """StandardError must direct errors to file or journal."""
        if service_content is None:
            pytest.skip("Service file does not exist yet")
        has_stderr = ('StandardError' in service_content or
                      'journal' in service_content.lower())
        assert has_stderr, (
            "Service must configure StandardError for error log capture"
        )


class TestServiceStartupCleanup:
    """Verify pre-start cleanup in service file."""

    def test_exec_start_pre_exists(self, service_content):
        """Service should have ExecStartPre for startup cleanup."""
        if service_content is None:
            pytest.skip("Service file does not exist yet")
        assert 'ExecStartPre' in service_content, (
            "Service should use ExecStartPre to clean up partial videos "
            "and temp files from unclean shutdowns"
        )


class TestServiceRestartPolicy:
    """Verify restart and recovery configuration."""

    def test_restart_always(self, service_content):
        """Service must restart on failure."""
        if service_content is None:
            pytest.skip("Service file does not exist yet")
        assert 'Restart=always' in service_content, (
            "Service must have Restart=always for automatic recovery"
        )

    def test_restart_sec_reasonable(self, service_content):
        """RestartSec should be between 5 and 30 seconds."""
        if service_content is None:
            pytest.skip("Service file does not exist yet")
        for line in service_content.splitlines():
            if line.strip().startswith('RestartSec='):
                value = int(line.split('=')[1].strip())
                assert 5 <= value <= 30, (
                    f"RestartSec={value} out of range. "
                    "Should be 5-30 seconds."
                )

    def test_runs_as_pi_user(self, service_content):
        """Service must run as 'pi' user, not root."""
        if service_content is None:
            pytest.skip("Service file does not exist yet")
        assert 'User=pi' in service_content, (
            "Service must run as 'pi' user for security"
        )
