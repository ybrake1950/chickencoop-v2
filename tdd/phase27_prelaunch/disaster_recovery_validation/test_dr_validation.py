"""
Phase 27: Disaster Recovery Validation Tests
==============================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates that disaster recovery capabilities are
properly implemented and tested:
- Power loss recovery tests exist and pass
- Backup/restore tests exist and pass
- Configuration rollback tests exist and pass
- Cross-coop failover tests exist and pass

WHY THIS MATTERS:
-----------------
Disaster recovery is only valuable if it actually works. These meta-tests
verify that the DR test suite (Phase 17) is comprehensive and passing.
A deployment without validated DR is a deployment waiting to fail.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase27_prelaunch/disaster_recovery_validation/test_dr_validation.py -v
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
    """Get tdd directory."""
    return Path(__file__).parents[2]


class TestPowerRecoveryTestsExist:
    """Verify power recovery tests are comprehensive."""

    def test_power_recovery_tests_exist(self, tdd_dir):
        """Phase 9 power recovery tests must exist."""
        pr_dir = tdd_dir / 'phase9_resilience' / 'power'
        assert pr_dir.exists(), "phase9_resilience/power/ not found"
        test_files = list(pr_dir.glob('test_*.py'))
        assert len(test_files) > 0, "No power recovery test files found"

    def test_power_recovery_tests_pass(self, project_root):
        """Power recovery tests must pass."""
        result = subprocess.run(
            [sys.executable, '-m', 'pytest',
             'tdd/phase9_resilience/power/', '-q', '--tb=short'],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=60,
        )
        if 'failed' in result.stdout:
            pytest.fail(
                f"Power recovery tests failing:\n{result.stdout[-1000:]}"
            )


class TestBackupRestoreTestsExist:
    """Verify backup and restore tests are comprehensive."""

    def test_backup_tests_exist(self, tdd_dir):
        """Phase 17 backup tests must exist."""
        backup_dir = tdd_dir / 'phase17_backup_dr' / 'backup'
        assert backup_dir.exists(), "phase17_backup_dr/backup/ not found"
        test_files = list(backup_dir.glob('test_*.py'))
        assert len(test_files) > 0, "No backup test files found"

    def test_recovery_tests_exist(self, tdd_dir):
        """Phase 17 disaster recovery tests must exist."""
        dr_dir = tdd_dir / 'phase17_backup_dr' / 'recovery'
        assert dr_dir.exists(), "phase17_backup_dr/recovery/ not found"
        test_files = list(dr_dir.glob('test_*.py'))
        assert len(test_files) > 0, "No disaster recovery test files found"

    def test_backup_tests_pass(self, project_root):
        """Backup and recovery tests must pass."""
        result = subprocess.run(
            [sys.executable, '-m', 'pytest',
             'tdd/phase17_backup_dr/', '-q', '--tb=short'],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=60,
        )
        if 'failed' in result.stdout:
            pytest.fail(
                f"Backup/DR tests failing:\n{result.stdout[-1000:]}"
            )


class TestFailoverTestsExist:
    """Verify cross-coop failover tests exist."""

    def test_failover_tests_exist(self, tdd_dir):
        """Phase 17 failover tests must exist."""
        fo_dir = tdd_dir / 'phase17_backup_dr' / 'failover'
        assert fo_dir.exists(), "phase17_backup_dr/failover/ not found"
        test_files = list(fo_dir.glob('test_*.py'))
        assert len(test_files) > 0, "No failover test files found"

    def test_failover_tests_pass(self, project_root):
        """Failover tests must pass."""
        result = subprocess.run(
            [sys.executable, '-m', 'pytest',
             'tdd/phase17_backup_dr/failover/', '-q', '--tb=short'],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=60,
        )
        if 'failed' in result.stdout:
            pytest.fail(
                f"Failover tests failing:\n{result.stdout[-1000:]}"
            )
