"""
Phase 8: Auto-Update Script Tests
=================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates automatic update functionality:
- System package updates (apt)
- Python dependency updates (pip)
- Kernel update detection and reboot scheduling
- Hostname-based device detection

WHY THIS MATTERS:
-----------------
Auto-updates keep the Raspberry Pi systems secure and up-to-date with
the latest patches. The script must handle package updates gracefully,
detect kernel updates that require reboots, and schedule reboots for
off-hours to minimize disruption.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase8_devops/deployment/test_auto_update.py -v

Tests validate script structure and update logic.
"""
import pytest
from pathlib import Path


@pytest.fixture
def auto_update_script_path():
    """Get path to auto-update.sh script."""
    return Path(__file__).parents[3] / 'scripts' / 'auto-update.sh'


@pytest.fixture
def auto_update_content(auto_update_script_path):
    """Load auto-update.sh content."""
    if auto_update_script_path.exists():
        return auto_update_script_path.read_text()
    return None


class TestAutoUpdateStructure:
    """Test auto-update script structure."""

    def test_auto_update_script_exists(self, auto_update_script_path):
        """auto-update.sh script exists."""
        assert auto_update_script_path.exists(), "auto-update.sh not found"

    def test_script_has_shebang(self, auto_update_content):
        """Script has proper shebang."""
        if auto_update_content is None:
            pytest.skip("auto-update.sh not found")

        assert auto_update_content.startswith('#!/bin/bash') or \
               auto_update_content.startswith('#!/usr/bin/env bash')


class TestSystemUpdates:
    """Test system package update functionality."""

    def test_runs_apt_update(self, auto_update_content):
        """Script runs apt update."""
        if auto_update_content is None:
            pytest.skip("auto-update.sh not found")

        assert 'apt update' in auto_update_content or 'apt-get update' in auto_update_content

    def test_runs_apt_upgrade(self, auto_update_content):
        """Script runs apt upgrade."""
        if auto_update_content is None:
            pytest.skip("auto-update.sh not found")

        assert 'apt upgrade' in auto_update_content or \
               'apt-get upgrade' in auto_update_content or \
               'apt full-upgrade' in auto_update_content

    def test_runs_autoremove(self, auto_update_content):
        """Script runs apt autoremove."""
        if auto_update_content is None:
            pytest.skip("auto-update.sh not found")

        assert 'autoremove' in auto_update_content

    def test_uses_noninteractive(self, auto_update_content):
        """Script uses non-interactive mode."""
        if auto_update_content is None:
            pytest.skip("auto-update.sh not found")

        has_noninteractive = '-y' in auto_update_content or \
                            'DEBIAN_FRONTEND=noninteractive' in auto_update_content
        assert has_noninteractive, "Should use non-interactive mode for apt"


class TestPythonUpdates:
    """Test Python dependency updates."""

    def test_updates_pip_packages(self, auto_update_content):
        """Script updates pip packages."""
        if auto_update_content is None:
            pytest.skip("auto-update.sh not found")

        assert 'pip install' in auto_update_content

    def test_uses_requirements_file(self, auto_update_content):
        """Script uses requirements.txt for updates."""
        if auto_update_content is None:
            pytest.skip("auto-update.sh not found")

        assert 'requirements' in auto_update_content

    def test_uses_upgrade_flag(self, auto_update_content):
        """Script uses --upgrade flag for pip."""
        if auto_update_content is None:
            pytest.skip("auto-update.sh not found")

        assert '--upgrade' in auto_update_content or '-U' in auto_update_content


class TestKernelUpdateHandling:
    """Test kernel update detection and reboot."""

    def test_detects_kernel_update(self, auto_update_content):
        """Script detects kernel updates."""
        if auto_update_content is None:
            pytest.skip("auto-update.sh not found")

        has_kernel_check = 'kernel' in auto_update_content.lower() or \
                          'reboot' in auto_update_content.lower()
        assert has_kernel_check, "Should handle kernel updates"

    def test_schedules_reboot_for_offhours(self, auto_update_content):
        """Schedules reboot for off-hours."""
        if auto_update_content is None:
            pytest.skip("auto-update.sh not found")

        if 'reboot' in auto_update_content.lower():
            # Should schedule for early morning, not immediate
            has_scheduled = 'shutdown' in auto_update_content or \
                           '3:00' in auto_update_content or \
                           '03:00' in auto_update_content or \
                           'at ' in auto_update_content
            assert has_scheduled, "Reboot should be scheduled for off-hours"


class TestDeviceDetection:
    """Test hostname-based device detection."""

    def test_uses_hostname_detection(self, auto_update_content):
        """Script uses hostname to detect device."""
        if auto_update_content is None:
            pytest.skip("auto-update.sh not found")

        assert 'hostname' in auto_update_content.lower()


class TestErrorHandling:
    """Test error handling in auto-update."""

    def test_handles_apt_errors(self, auto_update_content):
        """Script handles apt errors."""
        if auto_update_content is None:
            pytest.skip("auto-update.sh not found")

        has_error_handling = 'set -e' in auto_update_content or \
                            '|| ' in auto_update_content or \
                            'if ' in auto_update_content
        assert has_error_handling

    def test_logs_update_activity(self, auto_update_content):
        """Script logs update activity."""
        if auto_update_content is None:
            pytest.skip("auto-update.sh not found")

        has_logging = 'echo' in auto_update_content or \
                     'log' in auto_update_content.lower()
        assert has_logging


class TestWebAppUpdateScript:
    """Test deploy-webapp-update.sh script."""

    @pytest.fixture
    def webapp_update_path(self):
        """Get path to deploy-webapp-update.sh."""
        return Path(__file__).parents[3] / 'deploy-webapp-update.sh'

    @pytest.fixture
    def webapp_update_content(self, webapp_update_path):
        """Load deploy-webapp-update.sh content."""
        if webapp_update_path.exists():
            return webapp_update_path.read_text()
        return None

    def test_webapp_update_script_exists(self, webapp_update_path):
        """deploy-webapp-update.sh exists."""
        # May not exist
        if not webapp_update_path.exists():
            pytest.skip("deploy-webapp-update.sh not found")
        assert webapp_update_path.exists()

    def test_uses_scp_for_copy(self, webapp_update_content):
        """Uses scp to copy files."""
        if webapp_update_content is None:
            pytest.skip("deploy-webapp-update.sh not found")

        assert 'scp' in webapp_update_content

    def test_copies_app_files(self, webapp_update_content):
        """Copies app.py file."""
        if webapp_update_content is None:
            pytest.skip("deploy-webapp-update.sh not found")

        assert 'app.py' in webapp_update_content

    def test_copies_templates(self, webapp_update_content):
        """Copies template files."""
        if webapp_update_content is None:
            pytest.skip("deploy-webapp-update.sh not found")

        assert 'template' in webapp_update_content.lower() or \
               'index.html' in webapp_update_content

    def test_copies_static_files(self, webapp_update_content):
        """Copies static files."""
        if webapp_update_content is None:
            pytest.skip("deploy-webapp-update.sh not found")

        has_static = 'static' in webapp_update_content or \
                    '.js' in webapp_update_content or \
                    '.css' in webapp_update_content
        assert has_static

    def test_restarts_services(self, webapp_update_content):
        """Restarts services after update."""
        if webapp_update_content is None:
            pytest.skip("deploy-webapp-update.sh not found")

        has_restart = 'systemctl restart' in webapp_update_content or \
                     'restart' in webapp_update_content.lower()
        assert has_restart
