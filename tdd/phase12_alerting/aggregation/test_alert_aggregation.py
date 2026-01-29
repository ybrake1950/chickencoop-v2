"""
Phase 12: Alert Aggregation Tests
=================================

FUNCTIONALITY BEING TESTED:
---------------------------
- Debounce rapid repeated alerts
- Aggregate similar alerts into digest
- Cooldown periods between alerts
- Trend-based alert generation
- Predictive alerting

WHY THIS MATTERS:
-----------------
Without aggregation, users could receive hundreds of alerts during an
event. Smart aggregation reduces noise while ensuring important events
are communicated clearly.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase12_alerting/aggregation/test_alert_aggregation.py -v
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from src.alerting.aggregation import (
    AlertAggregator,
    AlertDebouncer,
    AlertDigest,
    TrendDetector,
    PredictiveAlert,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def debouncer():
    """Provide an alert debouncer."""
    return AlertDebouncer(window_seconds=60)


@pytest.fixture
def aggregator():
    """Provide an alert aggregator."""
    return AlertAggregator()


@pytest.fixture
def trend_detector():
    """Provide a trend detector."""
    return TrendDetector(
        rate_threshold=5.0,  # 5 degrees per hour
        window_minutes=30
    )


@pytest.fixture
def predictive_alert():
    """Provide a predictive alert engine."""
    return PredictiveAlert(threshold=100.0)


# =============================================================================
# TestAlertDebouncing
# =============================================================================

class TestAlertDebouncing:
    """Test alert debouncing."""

    def test_rapid_alerts_debounced(self, debouncer):
        """Rapid repeated alerts are debounced."""
        now = datetime.now(timezone.utc)

        # First alert should pass through
        result1 = debouncer.should_send(alert_type="temperature_high", timestamp=now)
        assert result1 is True

        # Second alert within window should be debounced
        result2 = debouncer.should_send(
            alert_type="temperature_high",
            timestamp=now + timedelta(seconds=5)
        )
        assert result2 is False

    def test_debounce_window_configurable(self):
        """Debounce window is configurable."""
        short = AlertDebouncer(window_seconds=10)
        long = AlertDebouncer(window_seconds=300)

        assert short.window_seconds == 10
        assert long.window_seconds == 300

    def test_first_alert_sent_immediately(self, debouncer):
        """First alert in series sent immediately."""
        result = debouncer.should_send(
            alert_type="humidity_high",
            timestamp=datetime.now(timezone.utc)
        )
        assert result is True

    def test_summary_sent_after_debounce(self, debouncer):
        """Summary sent after debounce window."""
        now = datetime.now(timezone.utc)

        debouncer.should_send(alert_type="temperature_high", timestamp=now)

        # Suppress 5 alerts during window
        for i in range(5):
            debouncer.should_send(
                alert_type="temperature_high",
                timestamp=now + timedelta(seconds=10 + i)
            )

        # After window expires, get summary
        summary = debouncer.get_summary(
            alert_type="temperature_high",
            timestamp=now + timedelta(seconds=120)
        )

        assert summary is not None
        assert summary.suppressed_count >= 5

    def test_different_types_not_debounced(self, debouncer):
        """Different alert types debounced separately."""
        now = datetime.now(timezone.utc)

        result1 = debouncer.should_send(alert_type="temperature_high", timestamp=now)
        result2 = debouncer.should_send(alert_type="humidity_high", timestamp=now)

        # Both should pass - they are different types
        assert result1 is True
        assert result2 is True


# =============================================================================
# TestAlertDigest
# =============================================================================

class TestAlertDigest:
    """Test alert digest aggregation."""

    def test_daily_digest_generated(self, aggregator):
        """Daily digest summarizes alerts."""
        # Add some alerts
        now = datetime.now(timezone.utc)
        for i in range(10):
            aggregator.add_alert({
                "type": "temperature_high",
                "value": 95 + i,
                "timestamp": (now - timedelta(hours=i)).isoformat()
            })

        digest = aggregator.generate_digest(period="daily")

        assert digest is not None
        assert digest.total_alerts == 10

    def test_digest_includes_counts(self, aggregator):
        """Digest includes alert counts by type."""
        now = datetime.now(timezone.utc)
        for i in range(5):
            aggregator.add_alert({"type": "temperature_high", "timestamp": now.isoformat()})
        for i in range(3):
            aggregator.add_alert({"type": "humidity_high", "timestamp": now.isoformat()})

        digest = aggregator.generate_digest(period="daily")

        assert digest.counts_by_type["temperature_high"] == 5
        assert digest.counts_by_type["humidity_high"] == 3

    def test_digest_includes_extremes(self, aggregator):
        """Digest includes min/max values."""
        now = datetime.now(timezone.utc)
        values = [90, 95, 100, 85, 110]
        for v in values:
            aggregator.add_alert({
                "type": "temperature_high",
                "value": v,
                "timestamp": now.isoformat()
            })

        digest = aggregator.generate_digest(period="daily")

        assert digest.max_value == 110
        assert digest.min_value == 85

    def test_digest_time_configurable(self, aggregator):
        """Digest send time configurable."""
        aggregator.set_digest_schedule(hour=18, minute=0)

        assert aggregator.digest_hour == 18
        assert aggregator.digest_minute == 0

    def test_no_digest_if_no_alerts(self, aggregator):
        """Digest skipped if no alerts to report."""
        digest = aggregator.generate_digest(period="daily")

        assert digest is None or digest.total_alerts == 0


# =============================================================================
# TestCooldownPeriods
# =============================================================================

class TestCooldownPeriods:
    """Test cooldown between repeated alerts."""

    def test_cooldown_enforced(self, aggregator):
        """Cooldown period enforced between alerts."""
        aggregator.set_cooldown("temperature_high", seconds=300)
        now = datetime.now(timezone.utc)

        result1 = aggregator.check_cooldown("temperature_high", timestamp=now)
        assert result1.can_send is True

        # Mark as sent
        aggregator.mark_sent("temperature_high", timestamp=now)

        # Within cooldown
        result2 = aggregator.check_cooldown(
            "temperature_high",
            timestamp=now + timedelta(seconds=60)
        )
        assert result2.can_send is False

    def test_cooldown_per_alert_type(self, aggregator):
        """Cooldown tracked per alert type."""
        aggregator.set_cooldown("temperature_high", seconds=300)
        aggregator.set_cooldown("humidity_high", seconds=600)
        now = datetime.now(timezone.utc)

        aggregator.mark_sent("temperature_high", timestamp=now)

        # Humidity should not be affected by temperature cooldown
        result = aggregator.check_cooldown("humidity_high", timestamp=now)
        assert result.can_send is True

    def test_cooldown_duration_configurable(self, aggregator):
        """Cooldown duration configurable."""
        aggregator.set_cooldown("temperature_high", seconds=120)
        aggregator.set_cooldown("motion_detected", seconds=30)

        assert aggregator.get_cooldown("temperature_high") == 120
        assert aggregator.get_cooldown("motion_detected") == 30

    def test_cooldown_resets_on_resolve(self, aggregator):
        """Cooldown resets when condition resolves."""
        now = datetime.now(timezone.utc)
        aggregator.set_cooldown("temperature_high", seconds=300)
        aggregator.mark_sent("temperature_high", timestamp=now)

        # Condition resolves (temp back to normal)
        aggregator.mark_resolved("temperature_high")

        # Should be able to send again immediately
        result = aggregator.check_cooldown(
            "temperature_high",
            timestamp=now + timedelta(seconds=10)
        )
        assert result.can_send is True

    def test_escalation_bypasses_cooldown(self, aggregator):
        """Escalated alerts bypass cooldown."""
        now = datetime.now(timezone.utc)
        aggregator.set_cooldown("temperature_high", seconds=300)
        aggregator.mark_sent("temperature_high", timestamp=now)

        # Escalated alert should bypass cooldown
        result = aggregator.check_cooldown(
            "temperature_high",
            timestamp=now + timedelta(seconds=10),
            severity="critical"
        )
        assert result.can_send is True


# =============================================================================
# TestTrendAlerts
# =============================================================================

class TestTrendAlerts:
    """Test trend-based alert generation."""

    def test_rising_temperature_trend(self, trend_detector):
        """Alert on rapidly rising temperature."""
        now = datetime.now(timezone.utc)
        # Feed rapidly rising temperatures
        readings = [
            {"value": 70, "timestamp": (now - timedelta(minutes=30)).isoformat()},
            {"value": 75, "timestamp": (now - timedelta(minutes=20)).isoformat()},
            {"value": 82, "timestamp": (now - timedelta(minutes=10)).isoformat()},
            {"value": 90, "timestamp": now.isoformat()},
        ]

        for r in readings:
            trend_detector.add_reading(r)

        trend = trend_detector.detect_trend()

        assert trend is not None
        assert trend.direction == "rising"
        assert trend.rate_per_hour > 0

    def test_falling_temperature_trend(self, trend_detector):
        """Alert on rapidly falling temperature."""
        now = datetime.now(timezone.utc)
        readings = [
            {"value": 90, "timestamp": (now - timedelta(minutes=30)).isoformat()},
            {"value": 80, "timestamp": (now - timedelta(minutes=20)).isoformat()},
            {"value": 70, "timestamp": (now - timedelta(minutes=10)).isoformat()},
            {"value": 60, "timestamp": now.isoformat()},
        ]

        for r in readings:
            trend_detector.add_reading(r)

        trend = trend_detector.detect_trend()

        assert trend is not None
        assert trend.direction == "falling"
        assert trend.rate_per_hour < 0

    def test_trend_rate_configurable(self):
        """Trend rate threshold configurable."""
        detector = TrendDetector(rate_threshold=10.0, window_minutes=30)
        assert detector.rate_threshold == 10.0

    def test_trend_window_configurable(self):
        """Trend detection window configurable."""
        detector = TrendDetector(rate_threshold=5.0, window_minutes=60)
        assert detector.window_minutes == 60

    def test_trend_alert_includes_rate(self, trend_detector):
        """Trend alert includes rate of change."""
        now = datetime.now(timezone.utc)
        readings = [
            {"value": 70, "timestamp": (now - timedelta(minutes=30)).isoformat()},
            {"value": 90, "timestamp": now.isoformat()},
        ]

        for r in readings:
            trend_detector.add_reading(r)

        trend = trend_detector.detect_trend()

        assert trend is not None
        assert hasattr(trend, 'rate_per_hour')
        assert isinstance(trend.rate_per_hour, (int, float))


# =============================================================================
# TestPredictiveAlerts
# =============================================================================

class TestPredictiveAlerts:
    """Test predictive alerting."""

    def test_predict_threshold_breach(self, predictive_alert):
        """Predict when threshold will be breached."""
        now = datetime.now(timezone.utc)
        readings = [
            {"value": 80, "timestamp": (now - timedelta(minutes=30)).isoformat()},
            {"value": 85, "timestamp": (now - timedelta(minutes=20)).isoformat()},
            {"value": 90, "timestamp": (now - timedelta(minutes=10)).isoformat()},
            {"value": 95, "timestamp": now.isoformat()},
        ]

        for r in readings:
            predictive_alert.add_reading(r)

        prediction = predictive_alert.predict_breach()

        assert prediction is not None
        assert prediction.will_breach is True
        assert prediction.estimated_time is not None

    def test_advance_warning_time(self, predictive_alert):
        """Provide advance warning before breach."""
        now = datetime.now(timezone.utc)
        readings = [
            {"value": 80, "timestamp": (now - timedelta(minutes=30)).isoformat()},
            {"value": 90, "timestamp": (now - timedelta(minutes=15)).isoformat()},
            {"value": 95, "timestamp": now.isoformat()},
        ]

        for r in readings:
            predictive_alert.add_reading(r)

        prediction = predictive_alert.predict_breach()

        assert prediction is not None
        assert prediction.minutes_until_breach > 0

    def test_prediction_confidence(self, predictive_alert):
        """Include confidence level in prediction."""
        now = datetime.now(timezone.utc)
        readings = [
            {"value": 85, "timestamp": (now - timedelta(minutes=20)).isoformat()},
            {"value": 90, "timestamp": (now - timedelta(minutes=10)).isoformat()},
            {"value": 95, "timestamp": now.isoformat()},
        ]

        for r in readings:
            predictive_alert.add_reading(r)

        prediction = predictive_alert.predict_breach()

        assert prediction is not None
        assert 0.0 <= prediction.confidence <= 1.0

    def test_prediction_updates(self, predictive_alert):
        """Update prediction as data changes."""
        now = datetime.now(timezone.utc)

        # Rising trend
        for i in range(5):
            predictive_alert.add_reading({
                "value": 80 + i * 5,
                "timestamp": (now - timedelta(minutes=20 - i * 5)).isoformat()
            })

        prediction1 = predictive_alert.predict_breach()

        # Trend reverses
        predictive_alert.add_reading({
            "value": 85,
            "timestamp": (now + timedelta(minutes=5)).isoformat()
        })

        prediction2 = predictive_alert.predict_breach()

        # Prediction should update
        assert prediction1 is not None
        assert prediction2 is None or prediction2.minutes_until_breach > prediction1.minutes_until_breach
