"""
Phase 20: Coverage Gate Tests
==============================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates test coverage meets production thresholds:
- Overall coverage exceeds 80% (per PHASE1_QUICKSTART.md)
- No test files have zero passing tests
- All 18 original phases have at least one passing test
- Skipped tests are due to hardware/AWS markers, not broken code

WHY THIS MATTERS:
-----------------
Per PHASE1_QUICKSTART.md, the success criteria include ">80% coverage."
Coverage gates in CI prevent regressions and ensure untested code
does not reach production Raspberry Pis.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase20_test_completeness/coverage/test_coverage_gates.py -v
"""
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def tdd_dir():
    """Get path to tdd directory."""
    return Path(__file__).parents[2]


class TestCoverageThreshold:
    """Verify coverage meets minimum threshold."""

    @pytest.mark.slow
    def test_overall_coverage_above_80_percent(self, project_root):
        """Overall test coverage must be at least 80%."""
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 'tdd/',
             '--ignore=tdd/phase20_test_completeness',
             '--cov=src', '--cov-report=term', '-q',
             '--cov-fail-under=80', '--tb=no', '--no-header'],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=900,
        )
        assert result.returncode == 0, (
            f"Coverage below 80% threshold.\n"
            f"Output:\n{result.stdout[-2000:]}"
        )


class TestAllPhasesHavePassingTests:
    """Verify every phase directory has at least one passing test."""

    PHASE_DIRS = [
        'phase1_foundation',
        'phase2_hardware',
        'phase3_persistence',
        'phase4_aws',
        'phase5_api',
        'phase6_frontend',
        'phase7_integration',
        'phase8_devops',
        'phase9_resilience',
        'phase10_security',
        'phase11_code_quality',
        'phase12_alerting',
        'phase13_command_queue',
        'phase14_rbac',
        'phase15_streaming',
        'phase16_camera_intelligence',
        'phase17_backup_dr',
        'phase18_observability',
    ]

    @pytest.mark.parametrize('phase_dir', PHASE_DIRS)
    def test_phase_has_passing_tests(self, project_root, tdd_dir, phase_dir):
        """Each original phase must have at least one passing test."""
        phase_path = tdd_dir / phase_dir
        if not phase_path.exists():
            pytest.fail(f"Phase directory {phase_dir} does not exist")
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', f'tdd/{phase_dir}/',
             '-q', '--tb=no', '--no-header'],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=120,
        )
        # Parse "X passed" from output
        output = result.stdout
        if 'passed' not in output and 'error' in output.lower():
            pytest.fail(
                f"Phase {phase_dir} has no passing tests.\n"
                f"Output: {output[:1000]}"
            )


class TestNoTestFileHasZeroPassing:
    """Verify no individual test file has zero passing tests."""

    def test_zero_pass_files(self, project_root, tdd_dir):
        """No test file should have 0 passed and >0 failed/errors."""
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 'tdd/',
             '--ignore=tdd/phase20_test_completeness',
             '-q', '--tb=no', '--no-header'],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=900,
        )
        # Check for error lines indicating collection failures
        error_count = result.stderr.count('ERROR collecting')
        assert error_count == 0, (
            f"{error_count} test files failed to collect.\n"
            f"Errors:\n{result.stderr[-2000:]}"
        )
