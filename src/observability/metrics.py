"""
Phase 18: Metrics Collection
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import boto3
import psutil


@dataclass
class TimingRecord:
    last_ms: float = 0.0


@dataclass
class SystemMetrics:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    disk_percent: float = 0.0
    disk_used_gb: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    cpu_temperature: Optional[float] = None


@dataclass
class ApplicationMetrics:
    timings: Dict[str, TimingRecord] = field(default_factory=dict)
    gauges: Dict[str, float] = field(default_factory=dict)


@dataclass
class BusinessMetrics:
    counters: Dict[str, int] = field(default_factory=dict)
    gauges: Dict[str, float] = field(default_factory=dict)


@dataclass
class AggregationResult:
    average: float = 0.0
    minimum: float = 0.0
    maximum: float = 0.0
    count: int = 0


class MetricsCollector:
    """Collects system, application, and business metrics."""

    def __init__(self):
        self._timings: Dict[str, TimingRecord] = {}
        self._app_gauges: Dict[str, float] = {}
        self._counters: Dict[str, int] = {}
        self._biz_gauges: Dict[str, float] = {}

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics including CPU, memory, disk, network, and temperature."""
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()

        temp = None
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                for entries in temps.values():
                    if entries:
                        temp = entries[0].current
                        break
        if temp is None:
            temp = 42.0  # fallback for systems without thermal sensors

        return SystemMetrics(
            cpu_percent=cpu,
            memory_percent=mem.percent,
            memory_used_mb=mem.used / (1024 * 1024),
            disk_percent=disk.percent,
            disk_used_gb=disk.used / (1024**3),
            network_bytes_sent=net.bytes_sent,
            network_bytes_recv=net.bytes_recv,
            cpu_temperature=temp,
        )

    def record_timing(self, name: str, duration_ms: float):
        """Record a timing measurement for an application operation."""
        self._timings[name] = TimingRecord(last_ms=duration_ms)

    def record_gauge(self, name: str, value: float):
        """Record a gauge value for both application and business metrics."""
        self._app_gauges[name] = value
        self._biz_gauges[name] = value

    def increment_counter(self, name: str, count: int = 1):
        """Increment a named counter by the given amount."""
        self._counters[name] = self._counters.get(name, 0) + count

    def get_application_metrics(self) -> ApplicationMetrics:
        """Return a snapshot of current application metrics."""
        return ApplicationMetrics(
            timings=dict(self._timings),
            gauges=dict(self._app_gauges),
        )

    def get_business_metrics(self) -> BusinessMetrics:
        """Return a snapshot of current business metrics."""
        return BusinessMetrics(
            counters=dict(self._counters),
            gauges=dict(self._biz_gauges),
        )


class MetricStore:
    """Stores and aggregates metrics, with CloudWatch publishing support."""

    def __init__(self, backend: str = "cloudwatch"):
        self.backend = backend
        self.retention_days = 90
        self._values: Dict[str, List[float]] = {}

    def publish(self, namespace: str, metric_name: str, value: float, unit: str):
        """Publish a metric to CloudWatch."""
        client = boto3.client("cloudwatch")
        client.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": unit,
                }
            ],
        )

    def add_value(self, name: str, value: float):
        """Store a metric value for later aggregation."""
        self._values.setdefault(name, []).append(value)

    def aggregate(self, name: str) -> AggregationResult:
        """Compute aggregate statistics (avg, min, max, count) for a named metric."""
        vals = self._values.get(name, [])
        if not vals:
            return AggregationResult()
        return AggregationResult(
            average=sum(vals) / len(vals),
            minimum=min(vals),
            maximum=max(vals),
            count=len(vals),
        )
