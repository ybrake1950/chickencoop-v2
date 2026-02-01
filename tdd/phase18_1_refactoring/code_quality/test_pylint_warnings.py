"""
TDD Refactoring Tests: Pylint Code Quality Warnings

Verifies that source code is free of pylint warnings that indicate
code quality issues requiring refactoring. Per PHASE1_QUICKSTART.md:
"no linting errors: pylint src/"

RED phase: 192 pylint warnings exist across src/:
  - 45 unused arguments (W0613)
  - 42 unused imports (W0611)
  - 30 overly broad exception catches (W0718)
  - 22 unnecessary pass statements (W0107)
  - 11 logging f-string interpolation (W1203)
  - 9 unused variables (W0612)
  - 8 unspecified encoding (W1514)
  - 7 protected access (W0212)
  - 6 missing raise-from (W0707)
  - 6 global statement (W0603)
  - 3 missing timeout on requests.post (W3101)
  - Others: W1510, W0621, W0231

GREEN phase: Fix each warning category while keeping tests green.
REFACTOR phase: Verify no new warnings introduced.
"""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"


class TestPylintUnusedImports:
    """W0611: Unused imports should be removed."""

    def test_no_unused_imports(self):
        """No source file should have unused imports."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pylint",
                str(SRC_DIR),
                "--disable=all",
                "--enable=W0611",
                "--score=no",
            ],
            capture_output=True,
            text=True,
        )
        warnings = [
            line
            for line in result.stdout.splitlines()
            if "W0611" in line
        ]
        assert len(warnings) == 0, (
            f"{len(warnings)} unused import(s) found:\n"
            + "\n".join(warnings[:20])
        )


class TestPylintUnnecessaryPass:
    """W0107: Unnecessary pass statements should be removed."""

    def test_no_unnecessary_pass(self):
        """No source file should have unnecessary pass statements.

        Pass is only needed in empty function/class bodies. If a body
        has other statements, pass is redundant.
        """
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pylint",
                str(SRC_DIR),
                "--disable=all",
                "--enable=W0107",
                "--score=no",
            ],
            capture_output=True,
            text=True,
        )
        warnings = [
            line
            for line in result.stdout.splitlines()
            if "W0107" in line
        ]
        assert len(warnings) == 0, (
            f"{len(warnings)} unnecessary pass statement(s) found:\n"
            + "\n".join(warnings[:20])
        )


class TestPylintBroadExceptions:
    """W0718: Catching overly broad exceptions should be narrowed."""

    def test_no_broad_exception_catches(self):
        """Exception handlers should catch specific exception types,
        not bare Exception.
        """
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pylint",
                str(SRC_DIR),
                "--disable=all",
                "--enable=W0718",
                "--score=no",
            ],
            capture_output=True,
            text=True,
        )
        warnings = [
            line
            for line in result.stdout.splitlines()
            if "W0718" in line
        ]
        assert len(warnings) == 0, (
            f"{len(warnings)} broad exception catch(es) found:\n"
            + "\n".join(warnings[:20])
        )


class TestPylintMissingTimeout:
    """W3101: HTTP requests must specify a timeout."""

    def test_no_missing_timeouts(self):
        """All requests.post/get calls must include a timeout parameter
        to prevent indefinite hangs in production.
        """
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pylint",
                str(SRC_DIR),
                "--disable=all",
                "--enable=W3101",
                "--score=no",
            ],
            capture_output=True,
            text=True,
        )
        warnings = [
            line
            for line in result.stdout.splitlines()
            if "W3101" in line
        ]
        assert len(warnings) == 0, (
            f"{len(warnings)} missing timeout(s) on HTTP requests:\n"
            + "\n".join(warnings)
        )


class TestPylintMissingRaiseFrom:
    """W0707: Exception chaining should use 'raise X from Y'."""

    def test_no_missing_raise_from(self):
        """Re-raised exceptions should preserve the original traceback
        using 'raise NewError(...) from original_error'.
        """
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pylint",
                str(SRC_DIR),
                "--disable=all",
                "--enable=W0707",
                "--score=no",
            ],
            capture_output=True,
            text=True,
        )
        warnings = [
            line
            for line in result.stdout.splitlines()
            if "W0707" in line
        ]
        assert len(warnings) == 0, (
            f"{len(warnings)} missing 'raise from' found:\n"
            + "\n".join(warnings)
        )


class TestPylintLoggingFormat:
    """W1203: Logging calls should use lazy % formatting."""

    def test_no_fstring_in_logging(self):
        """Logging calls should use %s formatting, not f-strings,
        to avoid string interpolation when log level is disabled.
        """
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pylint",
                str(SRC_DIR),
                "--disable=all",
                "--enable=W1203",
                "--score=no",
            ],
            capture_output=True,
            text=True,
        )
        warnings = [
            line
            for line in result.stdout.splitlines()
            if "W1203" in line
        ]
        assert len(warnings) == 0, (
            f"{len(warnings)} f-string logging call(s) found:\n"
            + "\n".join(warnings[:20])
        )


class TestPylintUnusedVariables:
    """W0612: Unused variables should be removed."""

    def test_no_unused_variables(self):
        """No source file should have unused local variables."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pylint",
                str(SRC_DIR),
                "--disable=all",
                "--enable=W0612",
                "--score=no",
            ],
            capture_output=True,
            text=True,
        )
        warnings = [
            line
            for line in result.stdout.splitlines()
            if "W0612" in line
        ]
        assert len(warnings) == 0, (
            f"{len(warnings)} unused variable(s) found:\n"
            + "\n".join(warnings[:20])
        )


class TestPylintOverallWarningCount:
    """Aggregate gate: total pylint warning count must be zero."""

    def test_zero_pylint_warnings(self):
        """The entire src/ directory must have zero pylint warnings.

        This is the final refactoring gate that ensures all warning
        categories have been addressed.
        """
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pylint",
                str(SRC_DIR),
                "--disable=C,R",
                "--score=no",
            ],
            capture_output=True,
            text=True,
        )
        warnings = [
            line
            for line in result.stdout.splitlines()
            if line.startswith("src/")
        ]
        assert len(warnings) == 0, (
            f"{len(warnings)} total pylint warning(s) remain:\n"
            + "\n".join(warnings[:30])
            + ("\n..." if len(warnings) > 30 else "")
        )
