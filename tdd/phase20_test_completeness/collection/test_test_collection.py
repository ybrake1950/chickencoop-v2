"""
Phase 20: Test Collection Completeness Tests
=============================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates that the entire test suite can be collected
and executed without import errors:
- All test files in tdd/ are importable
- No missing module dependencies prevent test collection
- Test markers (unit, integration, e2e) are properly declared
- conftest.py fixtures are available to all phases

WHY THIS MATTERS:
-----------------
10 test files currently fail to collect due to missing runtime
dependencies (flask, cv2, psutil). A test that cannot be collected
provides zero coverage confidence. All tests must at minimum be
collectable for the CI pipeline to be meaningful.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase20_test_completeness/collection/test_test_collection.py -v
"""
import importlib
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def tdd_dir():
    """Get path to tdd directory."""
    return Path(__file__).parents[2]


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


class TestAllTestFilesCollectable:
    """Verify pytest can collect every test file without errors."""

    def _get_all_test_files(self, tdd_dir):
        """Find all test_*.py files in tdd/."""
        return sorted(tdd_dir.rglob('test_*.py'))

    def test_no_collection_errors(self, project_root):
        """pytest --collect-only should report zero errors."""
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 'tdd/', '--collect-only', '-q'],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )
        error_lines = [
            line for line in result.stderr.splitlines()
            if 'ERROR' in line and 'collecting' in line
        ]
        assert len(error_lines) == 0, (
            f"Test collection errors found:\n" +
            "\n".join(error_lines) +
            f"\n\nFull stderr:\n{result.stderr[-2000:]}"
        )

    def test_flask_importable(self):
        """Flask must be importable for Phase 5/6 tests."""
        try:
            import flask
            assert flask is not None
        except ImportError:
            pytest.fail(
                "flask is not installed. Required by Phase 5 (API) and "
                "Phase 6 (Frontend) tests. Add flask to requirements.txt."
            )

    def test_numpy_importable(self):
        """numpy must be importable for Phase 2/16 tests."""
        try:
            import numpy
            assert numpy is not None
        except ImportError:
            pytest.fail(
                "numpy is not installed. Required by Phase 2 (Hardware) "
                "and Phase 16 (Camera Intelligence) tests."
            )

    def test_cv2_importable(self):
        """cv2 must be importable for Phase 2/16 tests."""
        try:
            import cv2
            assert cv2 is not None
        except ImportError:
            pytest.fail(
                "opencv-python-headless is not installed. Required by "
                "Phase 2 (Motion) and Phase 16 (Chicken Counting) tests."
            )

    def test_psutil_importable(self):
        """psutil must be importable for Phase 18 tests."""
        try:
            import psutil
            assert psutil is not None
        except ImportError:
            pytest.fail(
                "psutil is not installed. Required by Phase 18 "
                "(Metrics Collection) tests."
            )


class TestPytestMarkers:
    """Verify test markers are properly configured."""

    def test_pytest_ini_exists(self, tdd_dir):
        """pytest.ini must exist with marker declarations."""
        pytest_ini = tdd_dir / 'pytest.ini'
        assert pytest_ini.exists(), "tdd/pytest.ini not found"

    def test_markers_declared(self, tdd_dir):
        """Required markers must be declared in pytest.ini."""
        pytest_ini = tdd_dir / 'pytest.ini'
        if not pytest_ini.exists():
            pytest.skip("pytest.ini not found")
        content = pytest_ini.read_text()
        expected_markers = ['unit', 'integration', 'e2e', 'slow', 'hardware']
        for marker in expected_markers:
            assert marker in content, (
                f"Marker '{marker}' not declared in pytest.ini"
            )


class TestConftestFixtures:
    """Verify shared fixtures are available."""

    def test_conftest_exists(self, tdd_dir):
        """tdd/conftest.py must exist with shared fixtures."""
        conftest = tdd_dir / 'conftest.py'
        assert conftest.exists(), "tdd/conftest.py not found"

    def test_conftest_has_flask_fixtures(self, tdd_dir):
        """conftest.py must provide flask_app and flask_client fixtures."""
        conftest = tdd_dir / 'conftest.py'
        content = conftest.read_text()
        assert 'flask_app' in content, "flask_app fixture missing from conftest.py"
        assert 'flask_client' in content, "flask_client fixture missing from conftest.py"

    def test_conftest_has_aws_fixtures(self, tdd_dir):
        """conftest.py must provide AWS mock fixtures."""
        conftest = tdd_dir / 'conftest.py'
        content = conftest.read_text()
        assert 'mock_s3_client' in content
        assert 'mock_iot_client' in content
        assert 'mock_sns_client' in content
