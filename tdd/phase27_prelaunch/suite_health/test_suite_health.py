"""
Phase 27: Test Suite Health Verification
==========================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates the overall health of the test suite:
- All tests pass (0 failures)
- No collection errors
- Type checking passes (mypy)
- Linting passes (pylint --errors-only)
- Code formatting is consistent (black --check)

WHY THIS MATTERS:
-----------------
Per PHASE1_QUICKSTART.md, success criteria include "All tests pass,"
">80% coverage," and "No linting errors." This phase gates production
deployment on meeting those criteria.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase27_prelaunch/suite_health/test_suite_health.py -v
"""
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


class TestAllTestsPass:
    """Verify the full test suite passes."""

    @pytest.mark.slow
    def test_full_suite_zero_failures(self, project_root):
        """Full test suite must have 0 failures."""
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 'tdd/',
             '-q', '--tb=no', '--no-header',
             # Exclude slow meta-tests to avoid recursion
             '--ignore=tdd/phase27_prelaunch'],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=300,
        )
        # Check for "X failed" in output
        if 'failed' in result.stdout:
            pytest.fail(
                f"Test failures detected:\n{result.stdout[-2000:]}"
            )

    @pytest.mark.slow
    def test_zero_collection_errors(self, project_root):
        """No test files should fail to collect."""
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 'tdd/',
             '--collect-only', '-q',
             '--ignore=tdd/phase27_prelaunch'],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=120,
        )
        error_count = result.stderr.count('ERROR collecting')
        assert error_count == 0, (
            f"{error_count} collection errors:\n{result.stderr[-2000:]}"
        )


class TestTypeChecking:
    """Verify type checking passes."""

    @pytest.mark.slow
    def test_mypy_passes(self, project_root):
        """mypy src/ should pass with no errors."""
        result = subprocess.run(
            [sys.executable, '-m', 'mypy', 'src/',
             '--ignore-missing-imports', '--no-error-summary'],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=120,
        )
        if result.returncode != 0:
            # Count actual errors (not notes)
            errors = [l for l in result.stdout.splitlines()
                      if ': error:' in l]
            if errors:
                pytest.fail(
                    f"mypy found {len(errors)} errors:\n" +
                    "\n".join(errors[:20])
                )


class TestLinting:
    """Verify linting passes."""

    @pytest.mark.slow
    def test_pylint_no_errors(self, project_root):
        """pylint src/ --errors-only should pass."""
        result = subprocess.run(
            [sys.executable, '-m', 'pylint', 'src/', '--errors-only',
             '--disable=import-error'],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=120,
        )
        if result.returncode != 0:
            errors = result.stdout.strip()
            if errors:
                pytest.fail(
                    f"pylint errors found:\n{errors[:2000]}"
                )


class TestCodeFormatting:
    """Verify code formatting is consistent."""

    @pytest.mark.slow
    def test_black_formatting(self, project_root):
        """black --check src/ should pass."""
        result = subprocess.run(
            [sys.executable, '-m', 'black', '--check', 'src/'],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=60,
        )
        if result.returncode != 0:
            reformatted = [l for l in result.stderr.splitlines()
                           if 'would reformat' in l]
            pytest.fail(
                f"black would reformat {len(reformatted)} files:\n" +
                "\n".join(reformatted[:20])
            )
