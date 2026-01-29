"""
Phase 18: Performance Monitoring Tests
======================================

FUNCTIONALITY BEING TESTED:
---------------------------
- Performance baseline establishment
- Anomaly detection
- Automated optimization suggestions
- Capacity planning data

WHY THIS MATTERS:
-----------------
Continuous performance monitoring catches degradation before users
notice. Baselines and anomaly detection enable proactive fixes.
Capacity planning prevents running out of resources.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase18_observability/performance/test_performance_monitoring.py -v
"""
import pytest
from unittest.mock import MagicMock

from src.observability.performance import (
    PerformanceMonitor,
    BaselineCalculator,
    AnomalyDetector,
    OptimizationAdvisor,
    CapacityPlanner,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def monitor():
    """Provide a performance monitor."""
    return PerformanceMonitor()


@pytest.fixture
def baseline():
    """Provide a baseline calculator."""
    return BaselineCalculator()


@pytest.fixture
def anomaly_detector():
    """Provide an anomaly detector."""
    return AnomalyDetector(threshold_stddev=2.0)


@pytest.fixture
def advisor():
    """Provide an optimization advisor."""
    return OptimizationAdvisor()


@pytest.fixture
def planner():
    """Provide a capacity planner."""
    return CapacityPlanner()


# =============================================================================
# TestPerformanceBaselines
# =============================================================================

class TestPerformanceBaselines:
    """Test performance baseline establishment."""

    def test_baseline_calculated(self, baseline):
        """Performance baselines calculated."""
        samples = [100, 105, 95, 110, 98, 102, 97, 103]
        baseline.add_samples("upload_time", samples)
        result = baseline.calculate("upload_time")
        assert result is not None
        assert result.mean > 0
        assert result.stddev >= 0

    def test_baseline_per_operation(self, baseline):
        """Baselines tracked per operation type."""
        baseline.add_samples("upload_time", [100, 105, 95])
        baseline.add_samples("encoding_time", [500, 520, 480])
        upload = baseline.calculate("upload_time")
        encoding = baseline.calculate("encoding_time")
        assert upload.mean != encoding.mean

    def test_baseline_updated_periodically(self, baseline):
        """Baselines updated periodically."""
        baseline.add_samples("upload_time", [100, 105, 95])
        initial = baseline.calculate("upload_time")
        baseline.add_samples("upload_time", [200, 210, 195])
        baseline.recalculate("upload_time")
        updated = baseline.calculate("upload_time")
        assert updated.mean > initial.mean

    def test_baseline_excludes_outliers(self, baseline):
        """Baselines exclude statistical outliers."""
        samples = [100, 102, 98, 101, 99, 1000, 97, 103]  # 1000 is outlier
        baseline.add_samples("upload_time", samples, exclude_outliers=True)
        result = baseline.calculate("upload_time")
        assert result.mean < 200  # Mean should not be skewed by outlier


# =============================================================================
# TestAnomalyDetection
# =============================================================================

class TestAnomalyDetection:
    """Test anomaly detection."""

    def test_slow_operation_detected(self, anomaly_detector):
        """Slower than baseline detected."""
        anomaly_detector.set_baseline("upload_time", mean=100, stddev=10)
        result = anomaly_detector.check("upload_time", value=150)
        assert result.is_anomaly is True
        assert result.deviation > 0

    def test_anomaly_alert_generated(self, anomaly_detector):
        """Anomaly generates alert."""
        anomaly_detector.set_baseline("upload_time", mean=100, stddev=10)
        result = anomaly_detector.check("upload_time", value=150)
        assert result.is_anomaly is True
        assert result.alert is not None
        assert result.alert.severity in ("warning", "critical")

    def test_anomaly_threshold_configurable(self):
        """Anomaly threshold configurable."""
        strict = AnomalyDetector(threshold_stddev=1.0)
        relaxed = AnomalyDetector(threshold_stddev=3.0)
        assert strict.threshold_stddev < relaxed.threshold_stddev

        strict.set_baseline("op", mean=100, stddev=10)
        relaxed.set_baseline("op", mean=100, stddev=10)

        # Value at 2 stddev: strict detects, relaxed does not
        assert strict.check("op", value=125).is_anomaly is True
        assert relaxed.check("op", value=125).is_anomaly is False

    def test_transient_anomaly_debounced(self, anomaly_detector):
        """Transient anomalies debounced."""
        anomaly_detector.set_baseline("upload_time", mean=100, stddev=10)
        anomaly_detector.enable_debounce(min_occurrences=3)

        # Single anomaly should be debounced
        result = anomaly_detector.check("upload_time", value=150)
        assert result.alert_suppressed is True

        # After 3 occurrences, should alert
        anomaly_detector.check("upload_time", value=155)
        result = anomaly_detector.check("upload_time", value=160)
        assert result.alert_suppressed is False


# =============================================================================
# TestOptimizationSuggestions
# =============================================================================

class TestOptimizationSuggestions:
    """Test automated optimization suggestions."""

    def test_suggestion_for_slow_upload(self, advisor):
        """Suggest optimization for slow uploads."""
        advisor.report_metric("upload_time", value=5000, unit="ms")
        suggestions = advisor.get_suggestions()
        assert len(suggestions) >= 1
        assert any("upload" in s.description.lower() for s in suggestions)

    def test_suggestion_for_high_cpu(self, advisor):
        """Suggest optimization for high CPU."""
        advisor.report_metric("cpu_usage", value=95.0, unit="percent")
        suggestions = advisor.get_suggestions()
        assert len(suggestions) >= 1
        assert any("cpu" in s.description.lower() for s in suggestions)

    def test_suggestion_for_disk_usage(self, advisor):
        """Suggest cleanup for high disk usage."""
        advisor.report_metric("disk_usage", value=90.0, unit="percent")
        suggestions = advisor.get_suggestions()
        assert len(suggestions) >= 1
        assert any("disk" in s.description.lower() or "storage" in s.description.lower()
                    for s in suggestions)

    def test_suggestions_prioritized(self, advisor):
        """Suggestions prioritized by impact."""
        advisor.report_metric("cpu_usage", value=95.0, unit="percent")
        advisor.report_metric("disk_usage", value=60.0, unit="percent")
        suggestions = advisor.get_suggestions()
        assert len(suggestions) >= 2
        # Higher priority items first
        assert suggestions[0].priority >= suggestions[1].priority


# =============================================================================
# TestCapacityPlanning
# =============================================================================

class TestCapacityPlanning:
    """Test capacity planning."""

    def test_storage_projection(self, planner):
        """Project storage needs."""
        planner.add_usage_data("storage_gb", [
            (1, 10), (2, 12), (3, 14), (4, 16)  # (week, GB)
        ])
        projection = planner.project("storage_gb", weeks_ahead=12)
        assert projection is not None
        assert projection.projected_value > 16

    def test_bandwidth_projection(self, planner):
        """Project bandwidth needs."""
        planner.add_usage_data("bandwidth_mbps", [
            (1, 5), (2, 6), (3, 7), (4, 8)
        ])
        projection = planner.project("bandwidth_mbps", weeks_ahead=8)
        assert projection is not None
        assert projection.projected_value > 8

    def test_growth_trend_analysis(self, planner):
        """Analyze growth trends."""
        planner.add_usage_data("storage_gb", [
            (1, 10), (2, 12), (3, 14), (4, 16)
        ])
        trend = planner.analyze_trend("storage_gb")
        assert trend is not None
        assert trend.direction == "increasing"
        assert trend.growth_rate > 0

    def test_capacity_alerts(self, planner):
        """Alert before capacity exhausted."""
        planner.set_capacity("storage_gb", max_value=50)
        planner.add_usage_data("storage_gb", [
            (1, 30), (2, 35), (3, 40), (4, 45)
        ])
        alert = planner.check_capacity("storage_gb")
        assert alert is not None
        assert alert.weeks_until_full > 0
        assert alert.severity in ("warning", "critical")
