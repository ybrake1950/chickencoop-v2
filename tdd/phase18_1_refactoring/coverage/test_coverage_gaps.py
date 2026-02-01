"""
TDD Refactoring Tests: Coverage Gap Verification

Verifies that all source modules meet the >80% coverage threshold
required by PHASE1_QUICKSTART.md success criteria.

RED phase: 12+ files are below 80% coverage:
  - src/persistence/repositories/video.py (39%)
  - src/hardware/sensors/humidity.py (58%)
  - src/services/video_service.py (60%)
  - src/persistence/repositories/user.py (67%)
  - src/services/sensor_service.py (67%)
  - src/hardware/sensors/temperature.py (69%)
  - src/hardware/camera/interface.py (69%)
  - src/hardware/sensors/combined.py (70%)
  - src/hardware/camera/factory.py (72%)
  - src/security/auth.py (73%)
  - src/utils/process.py (75%)
  - src/hardware/camera/base.py (78%)
  - src/persistence/base.py (78%)
  - src/persistence/repositories/sensor.py (77%)

GREEN phase: Add tests to cover missing branches/lines in each file.
REFACTOR phase: Ensure new tests are meaningful, not just coverage padding.
"""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
TDD_DIR = PROJECT_ROOT / "tdd"

MINIMUM_COVERAGE = 80

# Files that were below 80% coverage and must be improved
LOW_COVERAGE_FILES = [
    "src/persistence/repositories/video.py",
    "src/hardware/sensors/humidity.py",
    "src/services/video_service.py",
    "src/persistence/repositories/user.py",
    "src/services/sensor_service.py",
    "src/hardware/sensors/temperature.py",
    "src/hardware/camera/interface.py",
    "src/hardware/sensors/combined.py",
    "src/hardware/camera/factory.py",
    "src/security/auth.py",
    "src/utils/process.py",
    "src/hardware/camera/base.py",
    "src/persistence/base.py",
    "src/persistence/repositories/sensor.py",
]

# Phases 1-18 test directories
PHASE_DIRS = [
    "phase1_foundation",
    "phase2_hardware",
    "phase3_persistence",
    "phase4_aws",
    "phase5_api",
    "phase6_frontend",
    "phase7_integration",
    "phase8_devops",
    "phase9_resilience",
    "phase10_security",
    "phase11_code_quality",
    "phase12_alerting",
    "phase13_command_queue",
    "phase14_rbac",
    "phase15_streaming",
    "phase16_camera_intelligence",
    "phase17_backup_dr",
    "phase18_observability",
]


def _run_coverage_report():
    """Run coverage once and parse results for all files.

    Returns a dict mapping relative file paths to coverage percentages.
    """
    test_dirs = [str(TDD_DIR / d) for d in PHASE_DIRS]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *test_dirs,
            f"--cov={SRC_DIR}",
            "--cov-report=term",
            "-q",
            "--no-header",
            "--tb=no",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    coverage = {}
    for line in result.stdout.splitlines():
        # Coverage lines look like: src/foo/bar.py  100  5  95%
        line = line.strip()
        if line.startswith("src/") and "%" in line:
            parts = line.split()
            filepath = parts[0]
            for part in reversed(parts):
                if part.endswith("%"):
                    pct = int(part.replace("%", ""))
                    coverage[filepath] = pct
                    break
    return coverage


# Module-level cache so we only run coverage once per test session
_coverage_cache = None


def get_coverage():
    global _coverage_cache
    if _coverage_cache is None:
        _coverage_cache = _run_coverage_report()
    return _coverage_cache


class TestOverallCoverage:
    """Verify the overall project meets the 80% coverage threshold."""

    def test_overall_coverage_above_threshold(self):
        """Total src/ coverage must be >= 80%."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                *[str(TDD_DIR / d) for d in PHASE_DIRS],
                f"--cov={SRC_DIR}",
                "--cov-report=term",
                "-q",
                "--no-header",
                "--tb=no",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        for line in result.stdout.splitlines():
            if line.strip().startswith("TOTAL"):
                parts = line.split()
                for part in reversed(parts):
                    if part.endswith("%"):
                        pct = int(part.replace("%", ""))
                        assert pct >= MINIMUM_COVERAGE, (
                            f"Overall coverage is {pct}%, "
                            f"must be >= {MINIMUM_COVERAGE}%"
                        )
                        return
        pytest.fail("Could not determine overall coverage percentage")


class TestLowCoverageFiles:
    """Verify each previously-low-coverage file now meets the threshold."""

    @pytest.mark.parametrize("filepath", LOW_COVERAGE_FILES)
    def test_file_meets_coverage_threshold(self, filepath):
        """Each source file must individually meet >= 80% coverage."""
        coverage = get_coverage()
        if filepath not in coverage:
            pytest.skip(f"No coverage data for {filepath}")
        pct = coverage[filepath]
        assert pct >= MINIMUM_COVERAGE, (
            f"{filepath} coverage is {pct}%, must be >= {MINIMUM_COVERAGE}%"
        )
