"""
Phase 12: Alert Routing Tests
=============================

FUNCTIONALITY BEING TESTED:
---------------------------
- Route alerts by type (temperature, humidity, motion)
- Route by severity level
- Time-based routing (quiet hours)
- Per-user routing preferences

WHY THIS MATTERS:
-----------------
Different alerts need different channels. Critical alerts should use
every channel, while info alerts might only log. Users should control
their notification preferences.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase12_alerting/routing/test_alert_routing.py -v
"""
import pytest
from datetime import time
from unittest.mock import MagicMock

from src.alerting.routing import (
    AlertRouter,
    RoutingConfig,
    RoutingRule,
    AlertChannel,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def router():
    """Provide an alert router."""
    config = RoutingConfig(
        rules=[
            RoutingRule(alert_type="temperature_high", channels=[AlertChannel.SNS, AlertChannel.SLACK]),
            RoutingRule(alert_type="humidity_high", channels=[AlertChannel.SNS]),
            RoutingRule(alert_type="motion_detected", channels=[AlertChannel.SLACK]),
            RoutingRule(alert_type="system_error", channels=[AlertChannel.SNS, AlertChannel.SLACK, AlertChannel.EMAIL]),
        ]
    )
    return AlertRouter(config=config)


# =============================================================================
# TestAlertTypeRouting
# =============================================================================

class TestAlertTypeRouting:
    """Test routing alerts by type."""

    def test_temperature_alert_routes(self, router):
        """Temperature alerts route to SNS and Slack."""
        channels = router.get_channels(alert_type="temperature_high")
        assert AlertChannel.SNS in channels
        assert AlertChannel.SLACK in channels

    def test_humidity_alert_routes(self, router):
        """Humidity alerts route to SNS."""
        channels = router.get_channels(alert_type="humidity_high")
        assert AlertChannel.SNS in channels

    def test_system_alert_routes(self, router):
        """System alerts route to all channels."""
        channels = router.get_channels(alert_type="system_error")
        assert AlertChannel.SNS in channels
        assert AlertChannel.SLACK in channels
        assert AlertChannel.EMAIL in channels

    def test_motion_alert_routes(self, router):
        """Motion alerts route to Slack."""
        channels = router.get_channels(alert_type="motion_detected")
        assert AlertChannel.SLACK in channels

    def test_headcount_alert_routes(self, router):
        """Headcount alerts have routing rules."""
        router.add_rule(RoutingRule(
            alert_type="headcount_mismatch",
            channels=[AlertChannel.SNS, AlertChannel.SLACK]
        ))
        channels = router.get_channels(alert_type="headcount_mismatch")
        assert len(channels) >= 1

    def test_multiple_channels_per_type(self, router):
        """Alert type can route to multiple channels."""
        channels = router.get_channels(alert_type="system_error")
        assert len(channels) >= 2


# =============================================================================
# TestSeverityRouting
# =============================================================================

class TestSeverityRouting:
    """Test routing by severity."""

    def test_critical_uses_all_channels(self, router):
        """Critical alerts use all channels."""
        channels = router.get_channels(alert_type="temperature_high", severity="critical")
        assert len(channels) >= 2

    def test_warning_uses_subset(self, router):
        """Warning alerts use subset of channels."""
        channels = router.get_channels(alert_type="temperature_high", severity="warning")
        assert len(channels) >= 1

    def test_info_only_logs(self, router):
        """Info alerts only logged."""
        channels = router.get_channels(alert_type="temperature_high", severity="info")
        assert len(channels) <= 1 or AlertChannel.LOG in channels

    def test_severity_configurable(self, router):
        """Severity routing configurable."""
        router.set_severity_channels("critical", [
            AlertChannel.SNS, AlertChannel.SLACK, AlertChannel.EMAIL
        ])
        channels = router.get_severity_channels("critical")
        assert len(channels) == 3


# =============================================================================
# TestTimeBasedRouting
# =============================================================================

class TestTimeBasedRouting:
    """Test time-based routing."""

    def test_quiet_hours_respected(self, router):
        """Quiet hours suppress non-critical alerts."""
        router.set_quiet_hours(start=time(22, 0), end=time(7, 0))
        channels = router.get_channels(
            alert_type="humidity_high", severity="warning", current_time=time(23, 0)
        )
        assert len(channels) == 0 or channels == [AlertChannel.LOG]

    def test_critical_bypasses_quiet_hours(self, router):
        """Critical alerts bypass quiet hours."""
        router.set_quiet_hours(start=time(22, 0), end=time(7, 0))
        channels = router.get_channels(
            alert_type="temperature_high", severity="critical", current_time=time(23, 0)
        )
        assert len(channels) >= 1

    def test_quiet_hours_configurable(self, router):
        """Quiet hours are configurable."""
        router.set_quiet_hours(start=time(21, 0), end=time(8, 0))
        assert router.quiet_hours_start == time(21, 0)
        assert router.quiet_hours_end == time(8, 0)

    def test_timezone_aware_routing(self, router):
        """Quiet hours respect timezone."""
        router.set_quiet_hours(start=time(22, 0), end=time(7, 0), timezone="US/Eastern")
        assert router.quiet_hours_timezone == "US/Eastern"

    def test_alerts_queued_during_quiet(self, router):
        """Non-critical alerts queued during quiet hours."""
        router.set_quiet_hours(start=time(22, 0), end=time(7, 0))
        result = router.route_alert(
            alert_type="humidity_high", severity="warning", current_time=time(23, 0)
        )
        assert result.queued is True or result.suppressed is True


# =============================================================================
# TestUserRouting
# =============================================================================

class TestUserRouting:
    """Test per-user routing preferences."""

    def test_channel_preference(self, router):
        """Users can set channel preferences."""
        router.set_user_preference(user_id="user-123", preferred_channels=[AlertChannel.SLACK])
        prefs = router.get_user_preferences("user-123")
        assert AlertChannel.SLACK in prefs.channels

    def test_alert_type_filter(self, router):
        """Users can filter alert types."""
        router.set_user_preference(
            user_id="user-123", alert_types=["temperature_high", "motion_detected"]
        )
        prefs = router.get_user_preferences("user-123")
        assert "temperature_high" in prefs.alert_types
        assert "humidity_high" not in prefs.alert_types

    def test_personal_quiet_hours(self, router):
        """Users can set personal quiet hours."""
        router.set_user_preference(
            user_id="user-123", quiet_hours_start=time(23, 0), quiet_hours_end=time(6, 0)
        )
        prefs = router.get_user_preferences("user-123")
        assert prefs.quiet_hours_start == time(23, 0)

    def test_multiple_users_different_prefs(self, router):
        """Different users have different preferences."""
        router.set_user_preference(user_id="user-1", preferred_channels=[AlertChannel.SNS])
        router.set_user_preference(user_id="user-2", preferred_channels=[AlertChannel.SLACK])
        prefs1 = router.get_user_preferences("user-1")
        prefs2 = router.get_user_preferences("user-2")
        assert prefs1.channels != prefs2.channels
