"""
Phase 26: Raspberry Pi OS Preparation Tests
=============================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates that device setup documentation and scripts
properly cover OS-level preparation:
- Python 3.11+ requirement is documented
- System dependencies (opencv, libatlas) are listed
- I2C and camera interface enablement documented
- Hostname configuration for coop identity
- WiFi and static IP configuration documented

WHY THIS MATTERS:
-----------------
Raspberry Pis ship with a bare OS. Without clear preparation steps,
operators miss critical system dependencies, hardware interfaces stay
disabled, and the application fails on first run. These tests verify
the documentation and scripts cover all prerequisites.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase26_device_setup/os_preparation/test_os_preparation.py -v
"""
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def all_docs(project_root):
    """Concatenate all documentation content."""
    content = ''
    for ext in ['*.md', '*.txt', '*.rst']:
        for f in project_root.rglob(ext):
            if '.git' in str(f) or 'node_modules' in str(f):
                continue
            try:
                content += f.read_text() + '\n'
            except (UnicodeDecodeError, PermissionError):
                continue
    return content


@pytest.fixture
def all_scripts(project_root):
    """Concatenate all shell script content."""
    content = ''
    for f in project_root.rglob('*.sh'):
        try:
            content += f.read_text() + '\n'
        except (UnicodeDecodeError, PermissionError):
            continue
    return content


class TestPythonVersionDocumented:
    """Verify Python version requirement is documented."""

    def test_python_version_file_exists(self, project_root):
        """.python-version file must specify required Python version."""
        pv = project_root / '.python-version'
        assert pv.exists(), ".python-version file not found"

    def test_python_version_is_311_plus(self, project_root):
        """.python-version must require Python 3.11+."""
        pv = project_root / '.python-version'
        if not pv.exists():
            pytest.skip(".python-version does not exist")
        version = pv.read_text().strip()
        parts = version.split('.')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        assert major >= 3 and minor >= 11, (
            f"Python version {version} too old. Requires 3.11+"
        )


class TestSystemDependenciesDocumented:
    """Verify system-level dependencies are documented."""

    def test_opencv_dependency_documented(self, all_docs, all_scripts):
        """OpenCV system dependency must be documented or scripted."""
        combined = all_docs + all_scripts
        has_opencv = ('opencv' in combined.lower() or
                      'python3-opencv' in combined or
                      'libopencv' in combined)
        assert has_opencv, (
            "OpenCV system dependency not documented. "
            "Add: sudo apt install python3-opencv"
        )

    def test_libatlas_documented(self, all_docs, all_scripts):
        """libatlas (numpy dependency) must be documented."""
        combined = all_docs + all_scripts
        has_atlas = ('libatlas' in combined or
                     'atlas' in combined.lower())
        assert has_atlas, (
            "libatlas-base-dev not documented. "
            "Required by numpy on ARM: sudo apt install libatlas-base-dev"
        )


class TestHardwareInterfacesDocumented:
    """Verify hardware interface setup is documented."""

    def test_i2c_interface_documented(self, all_docs, all_scripts):
        """I2C interface enablement must be documented."""
        combined = all_docs + all_scripts
        has_i2c = ('i2c' in combined.lower() or
                   'raspi-config' in combined or
                   'dtparam=i2c' in combined)
        assert has_i2c, (
            "I2C interface setup not documented. "
            "Required for temperature/humidity sensors."
        )

    def test_camera_interface_documented(self, all_docs, all_scripts):
        """Camera interface enablement must be documented."""
        combined = all_docs + all_scripts
        has_camera = ('camera' in combined.lower() and
                      ('enable' in combined.lower() or
                       'raspi-config' in combined or
                       'dtoverlay' in combined))
        assert has_camera, (
            "Camera interface setup not documented. "
            "Required for video recording and chicken counting."
        )


class TestHostnameConfiguration:
    """Verify hostname-based coop identity is documented."""

    def test_hostname_setup_documented(self, all_docs, all_scripts):
        """Hostname configuration for coop identity must be documented."""
        combined = all_docs + all_scripts
        has_hostname = ('hostname' in combined.lower() or
                        'hostnamectl' in combined or
                        'coop1' in combined or
                        'coop2' in combined)
        assert has_hostname, (
            "Hostname configuration not documented. "
            "Each Pi must be named coop1 or coop2 for identity."
        )
