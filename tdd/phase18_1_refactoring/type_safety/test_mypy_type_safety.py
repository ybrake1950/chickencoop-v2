"""
TDD Refactoring Tests: Mypy Type Safety

Verifies that all source files pass mypy static type checking.
Per PHASE1_QUICKSTART.md success criteria, type checking with mypy
should pass for production readiness.

RED phase: 55 mypy errors exist across 17 source files.
GREEN phase: Fix type annotations and type errors in each file.
REFACTOR phase: Verify tests remain green after type fixes.
"""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"

# Files known to have mypy errors that must be fixed
FILES_WITH_TYPE_ERRORS = [
    "src/alerting/webhooks.py",
    "src/api/routes/dashboard_routes.py",
    "src/api/routes/settings_routes.py",
    "src/config/environment.py",
    "src/hardware/camera/picamera.py",
    "src/hardware/motion/detector.py",
    "src/models/base.py",
    "src/observability/performance.py",
    "src/observability/tracing.py",
    "src/persistence/csv_storage.py",
    "src/persistence/repositories/sensor.py",
    "src/persistence/repositories/user.py",
    "src/resilience/connection_retry.py",
    "src/resilience/local_storage.py",
    "src/security/validation.py",
    "src/utils/logging_setup.py",
    "src/utils/path_utils.py",
]


class TestMypyTypeSafety:
    """Verify source code passes mypy static type checking."""

    def test_mypy_is_installed(self):
        """Mypy must be available in the environment."""
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "mypy is not installed"

    def test_src_passes_mypy(self):
        """All source files must pass mypy with zero errors.

        Uses --ignore-missing-imports to avoid failures from
        third-party packages without type stubs.
        """
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                str(SRC_DIR),
                "--ignore-missing-imports",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            error_lines = [
                line
                for line in result.stdout.splitlines()
                if "error:" in line
            ]
            pytest.fail(
                f"mypy found {len(error_lines)} type error(s):\n"
                + "\n".join(error_lines[:25])
                + ("\n..." if len(error_lines) > 25 else "")
            )

    @pytest.mark.parametrize("filepath", FILES_WITH_TYPE_ERRORS)
    def test_individual_file_passes_mypy(self, filepath):
        """Each previously-failing file must now pass mypy individually."""
        full_path = PROJECT_ROOT / filepath
        if not full_path.exists():
            pytest.skip(f"File not found: {filepath}")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                str(full_path),
                "--ignore-missing-imports",
            ],
            capture_output=True,
            text=True,
        )
        error_lines = [
            line for line in result.stdout.splitlines() if "error:" in line
        ]
        assert len(error_lines) == 0, (
            f"mypy errors in {filepath}:\n" + "\n".join(error_lines)
        )
