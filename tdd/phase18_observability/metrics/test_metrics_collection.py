"""
Phase 18: Metrics Collection Tests
==================================

FUNCTIONALITY BEING TESTED:
---------------------------
- System metrics collection (CPU, memory, disk)
- Application metrics (processing time, queue depth)
- Custom business metrics
- Metric aggregation and storage

WHY THIS MATTERS:
-----------------
Metrics provide visibility into system health and performance.
They enable proactive issue detection, capacity planning, and
performance optimization.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase18_observability/metrics/test_metrics_collection.py -v
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.observability.metrics import (
    MetricsCollector,
    SystemMetrics,
    ApplicationMetrics,
    BusinessMetrics,
    MetricStore,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def collector():
    """Provide a metrics collector."""
    return MetricsCollector()


@pytest.fixture
def metric_store():
    """Provide a metric store."""
    return MetricStore(backend="cloudwatch")


# =============================================================================
# TestSystemMetrics
# =============================================================================

class TestSystemMetrics:
    """Test system metrics collection."""

    def test_cpu_usage_collected(self, collector):
        """CPU usage collected."""
        metrics = collector.collect_system_metrics()
        assert metrics.cpu_percent is not None
        assert 0.0 <= metrics.cpu_percent <= 100.0

    def test_memory_usage_collected(self, collector):
        """Memory usage collected."""
        metrics = collector.collect_system_metrics()
        assert metrics.memory_percent is not None
        assert 0.0 <= metrics.memory_percent <= 100.0
        assert metrics.memory_used_mb > 0

    def test_disk_usage_collected(self, collector):
        """Disk usage collected."""
        metrics = collector.collect_system_metrics()
        assert metrics.disk_percent is not None
        assert 0.0 <= metrics.disk_percent <= 100.0
        assert metrics.disk_used_gb >= 0

    def test_network_stats_collected(self, collector):
        """Network statistics collected."""
        metrics = collector.collect_system_metrics()
        assert metrics.network_bytes_sent >= 0
        assert metrics.network_bytes_recv >= 0

    def test_temperature_collected(self, collector):
        """Pi temperature collected."""
        metrics = collector.collect_system_metrics()
        assert metrics.cpu_temperature is not None
        assert metrics.cpu_temperature > 0


# =============================================================================
# TestApplicationMetrics
# =============================================================================

class TestApplicationMetrics:
    """Test application metrics collection."""

    def test_motion_detection_time(self, collector):
        """Motion detection processing time tracked."""
        collector.record_timing("motion_detection", duration_ms=45.2)
        metrics = collector.get_application_metrics()
        assert "motion_detection" in metrics.timings
        assert metrics.timings["motion_detection"].last_ms == 45.2

    def test_video_encoding_time(self, collector):
        """Video encoding time tracked."""
        collector.record_timing("video_encoding", duration_ms=1200.5)
        metrics = collector.get_application_metrics()
        assert "video_encoding" in metrics.timings
        assert metrics.timings["video_encoding"].last_ms == 1200.5

    def test_upload_latency(self, collector):
        """Upload latency tracked."""
        collector.record_timing("s3_upload", duration_ms=350.0)
        metrics = collector.get_application_metrics()
        assert "s3_upload" in metrics.timings
        assert metrics.timings["s3_upload"].last_ms == 350.0

    def test_api_response_time(self, collector):
        """API response time tracked."""
        collector.record_timing("api_response", duration_ms=85.3)
        metrics = collector.get_application_metrics()
        assert "api_response" in metrics.timings

    def test_queue_depth(self, collector):
        """Command queue depth tracked."""
        collector.record_gauge("queue_depth", value=12)
        metrics = collector.get_application_metrics()
        assert metrics.gauges["queue_depth"] == 12


# =============================================================================
# TestBusinessMetrics
# =============================================================================

class TestBusinessMetrics:
    """Test business metrics collection."""

    def test_videos_recorded_count(self, collector):
        """Videos recorded per day tracked."""
        collector.increment_counter("videos_recorded", count=5)
        metrics = collector.get_business_metrics()
        assert metrics.counters["videos_recorded"] == 5

    def test_alerts_sent_count(self, collector):
        """Alerts sent tracked."""
        collector.increment_counter("alerts_sent", count=3)
        metrics = collector.get_business_metrics()
        assert metrics.counters["alerts_sent"] == 3

    def test_headcount_accuracy(self, collector):
        """Headcount accuracy tracked."""
        collector.record_gauge("headcount_accuracy", value=0.95)
        metrics = collector.get_business_metrics()
        assert metrics.gauges["headcount_accuracy"] == 0.95

    def test_uptime_percentage(self, collector):
        """System uptime tracked."""
        collector.record_gauge("uptime_percent", value=99.9)
        metrics = collector.get_business_metrics()
        assert metrics.gauges["uptime_percent"] == 99.9
        assert metrics.gauges["uptime_percent"] <= 100.0


# =============================================================================
# TestMetricStorage
# =============================================================================

class TestMetricStorage:
    """Test metric storage."""

    @patch("src.observability.metrics.boto3.client")
    def test_metrics_sent_to_cloudwatch(self, mock_boto, metric_store):
        """Metrics sent to CloudWatch."""
        metric_store.publish(
            namespace="ChickenCoop",
            metric_name="CPUUsage",
            value=45.2,
            unit="Percent"
        )
        mock_boto.return_value.put_metric_data.assert_called_once()

    def test_metric_retention(self, metric_store):
        """Metrics retained per policy."""
        assert metric_store.retention_days > 0
        assert metric_store.retention_days <= 365

    def test_metric_aggregation(self, metric_store):
        """Metrics aggregated properly."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for v in values:
            metric_store.add_value("test_metric", v)
        agg = metric_store.aggregate("test_metric")
        assert agg.average == 30.0
        assert agg.minimum == 10.0
        assert agg.maximum == 50.0
        assert agg.count == 5
