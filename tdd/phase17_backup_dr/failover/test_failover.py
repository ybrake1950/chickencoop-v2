"""
Phase 17: Failover Tests
========================

FUNCTIONALITY BEING TESTED:
---------------------------
- Cross-coop failover detection
- Automatic failover triggering
- Failover notification
- Failback procedures

WHY THIS MATTERS:
-----------------
If one coop's Pi fails, another may be able to provide limited
monitoring. Automatic failover detection and notification helps
maintain visibility into chicken welfare.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase17_backup_dr/failover/test_failover.py -v
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from src.backup.failover import (
    FailoverManager,
    FailoverConfig,
    HealthChecker,
    FailoverState,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def failover_manager():
    """Provide a failover manager."""
    config = FailoverConfig(
        health_check_interval=30,
        failure_threshold=3,
        primary_coop="coop-1",
        backup_coop="coop-2",
    )
    return FailoverManager(config=config)


@pytest.fixture
def health_checker():
    """Provide a health checker."""
    return HealthChecker(interval_seconds=30, timeout_seconds=10)


# =============================================================================
# TestFailoverDetection
# =============================================================================

class TestFailoverDetection:
    """Test failover condition detection."""

    def test_detect_pi_offline(self, failover_manager):
        """Detect when Pi goes offline."""
        failover_manager.report_health("coop-1", healthy=False)
        status = failover_manager.get_status("coop-1")
        assert status.healthy is False
        assert status.consecutive_failures >= 1

    def test_detect_prolonged_offline(self, failover_manager):
        """Detect prolonged offline status."""
        for _ in range(5):
            failover_manager.report_health("coop-1", healthy=False)
        status = failover_manager.get_status("coop-1")
        assert status.consecutive_failures >= 5
        assert status.state == FailoverState.DEGRADED

    def test_health_check_threshold(self, failover_manager):
        """Health check failures trigger detection."""
        assert failover_manager.config.failure_threshold == 3
        for _ in range(2):
            failover_manager.report_health("coop-1", healthy=False)
        status = failover_manager.get_status("coop-1")
        assert status.state != FailoverState.FAILED

        failover_manager.report_health("coop-1", healthy=False)
        status = failover_manager.get_status("coop-1")
        assert status.state in (FailoverState.FAILED, FailoverState.DEGRADED)


# =============================================================================
# TestAutomaticFailover
# =============================================================================

class TestAutomaticFailover:
    """Test automatic failover."""

    def test_failover_triggered(self, failover_manager):
        """Failover triggered on detection."""
        for _ in range(failover_manager.config.failure_threshold):
            failover_manager.report_health("coop-1", healthy=False)
        result = failover_manager.check_and_failover()
        assert result.failover_triggered is True

    @patch("src.backup.failover.FailoverManager._activate_backup")
    def test_backup_coop_activated(self, mock_activate, failover_manager):
        """Backup monitoring activated."""
        for _ in range(failover_manager.config.failure_threshold):
            failover_manager.report_health("coop-1", healthy=False)
        failover_manager.check_and_failover()
        mock_activate.assert_called_once_with("coop-2")

    @patch("src.backup.failover.FailoverManager._send_notification")
    def test_failover_notification(self, mock_notify, failover_manager):
        """Failover notification sent."""
        for _ in range(failover_manager.config.failure_threshold):
            failover_manager.report_health("coop-1", healthy=False)
        failover_manager.check_and_failover()
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args
        assert "coop-1" in str(call_args)


# =============================================================================
# TestFailback
# =============================================================================

class TestFailback:
    """Test failback procedures."""

    def test_detect_recovery(self, failover_manager):
        """Detect when failed Pi recovers."""
        for _ in range(failover_manager.config.failure_threshold):
            failover_manager.report_health("coop-1", healthy=False)
        failover_manager.check_and_failover()

        failover_manager.report_health("coop-1", healthy=True)
        status = failover_manager.get_status("coop-1")
        assert status.healthy is True

    def test_automatic_failback(self, failover_manager):
        """Automatic failback to primary."""
        for _ in range(failover_manager.config.failure_threshold):
            failover_manager.report_health("coop-1", healthy=False)
        failover_manager.check_and_failover()

        for _ in range(3):
            failover_manager.report_health("coop-1", healthy=True)
        result = failover_manager.check_and_failback()
        assert result.failback_triggered is True
        assert result.primary_coop == "coop-1"

    @patch("src.backup.failover.FailoverManager._sync_data")
    def test_data_sync_on_failback(self, mock_sync, failover_manager):
        """Data synchronized on failback."""
        for _ in range(failover_manager.config.failure_threshold):
            failover_manager.report_health("coop-1", healthy=False)
        failover_manager.check_and_failover()

        for _ in range(3):
            failover_manager.report_health("coop-1", healthy=True)
        failover_manager.check_and_failback()
        mock_sync.assert_called_once()


# =============================================================================
# TestEdgeCases
# =============================================================================

class TestEdgeCases:
    """Test edge cases for full coverage."""

    def test_health_checker_init(self):
        """HealthChecker initializes with correct parameters."""
        checker = HealthChecker(interval_seconds=60, timeout_seconds=5)
        assert checker.interval_seconds == 60
        assert checker.timeout_seconds == 5

    def test_healthy_report_sets_healthy_state(self, failover_manager):
        """Healthy report on non-degraded coop sets HEALTHY state."""
        failover_manager.report_health("coop-1", healthy=True)
        status = failover_manager.get_status("coop-1")
        assert status.state == FailoverState.HEALTHY

    def test_no_failover_when_healthy(self, failover_manager):
        """No failover triggered when primary is healthy."""
        failover_manager.report_health("coop-1", healthy=True)
        result = failover_manager.check_and_failover()
        assert result.failover_triggered is False

    def test_no_failback_without_active_failover(self, failover_manager):
        """No failback triggered when failover is not active."""
        result = failover_manager.check_and_failback()
        assert result.failback_triggered is False
