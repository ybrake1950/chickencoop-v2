"""
TDD Refactoring Tests: Black Code Formatting

Verifies that all source files conform to Black's code formatting standard.
Per PHASE1_QUICKSTART.md success criteria: "no linting errors" includes
consistent formatting across the codebase.

RED phase: These tests fail because 78 source files need reformatting.
GREEN phase: Run `black src/` to auto-format all files.
REFACTOR phase: Verify tests remain green after formatting changes.
"""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"


class TestBlackFormatting:
    """Verify all source files pass Black formatting checks."""

    def test_black_is_installed(self):
        """Black formatter must be available in the environment."""
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "black is not installed"

    def test_src_directory_exists(self):
        """Source directory must exist for formatting checks."""
        assert SRC_DIR.is_dir(), f"Source directory not found: {SRC_DIR}"

    def test_all_source_files_formatted(self):
        """All Python files in src/ must conform to Black formatting.

        This is the core refactoring gate: no file should have
        formatting inconsistencies.
        """
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--quiet", str(SRC_DIR)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            # Get the list of files that need reformatting
            detail = subprocess.run(
                [sys.executable, "-m", "black", "--check", str(SRC_DIR)],
                capture_output=True,
                text=True,
            )
            unformatted = [
                line.replace("would reformat ", "")
                for line in detail.stderr.splitlines()
                if line.startswith("would reformat")
            ]
            pytest.fail(
                f"{len(unformatted)} file(s) need Black formatting:\n"
                + "\n".join(f"  - {f}" for f in unformatted[:20])
                + ("\n  ..." if len(unformatted) > 20 else "")
            )

    def test_no_python_files_excluded_from_check(self):
        """Every .py file under src/ must be checked by Black."""
        py_files = list(SRC_DIR.rglob("*.py"))
        assert len(py_files) > 0, "No Python files found in src/"
        # Ensure we have a reasonable number of files
        assert len(py_files) >= 60, (
            f"Expected at least 60 Python files in src/, found {len(py_files)}. "
            "Some modules may be missing."
        )
