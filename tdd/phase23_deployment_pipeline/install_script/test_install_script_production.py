"""
Phase 23: Install Script Production Tests
===========================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates scripts/install-services.sh:
- Uses correct paths (chickencoop-v2)
- Creates virtual environment
- Installs pip dependencies
- Provisions or documents IoT certificate setup
- Sets correct file permissions

WHY THIS MATTERS:
-----------------
install-services.sh is run once per Raspberry Pi during initial setup.
Incorrect paths or missing steps mean the device never starts monitoring.
A reliable install script is the difference between a 10-minute setup
and hours of debugging on headless devices.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase23_deployment_pipeline/install_script/test_install_script_production.py -v
"""
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def install_script_path(project_root):
    """Get path to install-services.sh."""
    return project_root / 'scripts' / 'install-services.sh'


@pytest.fixture
def install_content(install_script_path):
    """Load install script content."""
    if install_script_path.exists():
        return install_script_path.read_text()
    return None


class TestInstallScriptExists:
    """Verify install script exists and is executable."""

    def test_install_script_exists(self, install_script_path):
        """scripts/install-services.sh must exist."""
        assert install_script_path.exists(), (
            "scripts/install-services.sh not found"
        )

    def test_install_script_is_bash(self, install_content):
        """Install script must start with bash shebang."""
        if install_content is None:
            pytest.skip("Install script does not exist")
        assert install_content.startswith('#!/bin/bash') or \
               install_content.startswith('#!/usr/bin/env bash'), (
            "Install script must start with #!/bin/bash"
        )


class TestInstallScriptPaths:
    """Verify install script uses correct project paths."""

    def test_uses_correct_project_path(self, install_content):
        """Install script must reference chickencoop-v2 path."""
        if install_content is None:
            pytest.skip("Install script does not exist")
        if 'chickencoop' in install_content:
            lines = [l for l in install_content.splitlines()
                     if 'chickencoop' in l and not l.strip().startswith('#')]
            for line in lines:
                if 'chickencoop' in line and 'chickencoop-v2' not in line:
                    if '$' not in line and '{' not in line:
                        pytest.fail(
                            f"Install script uses old path: {line.strip()}"
                        )


class TestInstallScriptVirtualEnv:
    """Verify install script sets up virtual environment."""

    def test_creates_virtual_environment(self, install_content):
        """Install script should create a Python virtual environment."""
        if install_content is None:
            pytest.skip("Install script does not exist")
        has_venv = ('python3 -m venv' in install_content or
                    'virtualenv' in install_content or
                    'venv' in install_content)
        assert has_venv, (
            "Install script should create a virtual environment"
        )

    def test_installs_pip_dependencies(self, install_content):
        """Install script should install pip dependencies."""
        if install_content is None:
            pytest.skip("Install script does not exist")
        has_pip = ('pip install' in install_content or
                   'pip3 install' in install_content or
                   'requirements' in install_content)
        assert has_pip, (
            "Install script should install pip requirements"
        )


class TestInstallScriptCertificates:
    """Verify install script handles IoT certificates."""

    def test_references_certificates(self, install_content):
        """Install script should handle IoT certificate setup."""
        if install_content is None:
            pytest.skip("Install script does not exist")
        has_cert = ('cert' in install_content.lower() or
                    'certificate' in install_content.lower() or
                    'ssl' in install_content.lower() or
                    'iot' in install_content.lower())
        assert has_cert, (
            "Install script should handle IoT certificate provisioning"
        )

    def test_sets_certificate_permissions(self, install_content):
        """Install script should set restrictive cert permissions."""
        if install_content is None:
            pytest.skip("Install script does not exist")
        has_chmod = ('chmod' in install_content and
                     ('600' in install_content or '400' in install_content))
        assert has_chmod, (
            "Install script should set restrictive permissions on certs"
        )
