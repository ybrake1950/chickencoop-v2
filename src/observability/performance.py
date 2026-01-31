"""
Phase 18: Performance Monitoring Module
=======================================

Provides performance baseline establishment, anomaly detection,
optimization suggestions, and capacity planning.
"""

import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class BaselineResult:
    mean: float
    stddev: float


@dataclass
class AnomalyAlert:
    severity: str  # "warning" or "critical"


@dataclass
class AnomalyResult:
    is_anomaly: bool
    deviation: float = 0.0
    alert: Optional[AnomalyAlert] = None
    alert_suppressed: bool = False


@dataclass
class Suggestion:
    description: str
    priority: int  # higher = more urgent


@dataclass
class Projection:
    projected_value: float


@dataclass
class Trend:
    direction: str  # "increasing", "decreasing", "stable"
    growth_rate: float


@dataclass
class CapacityAlert:
    weeks_until_full: float
    severity: str  # "warning" or "critical"


class BaselineCalculator:
    """Calculates and caches performance baselines from sample data."""

    def __init__(self):
        self._samples: Dict[str, List[float]] = {}
        self._cache: Dict[str, BaselineResult] = {}

    def add_samples(self, operation: str, samples: List[float], exclude_outliers: bool = False):
        """Add performance samples for a given operation, optionally filtering outliers."""
        if exclude_outliers:
            samples = self._remove_outliers(samples)
        if operation not in self._samples:
            self._samples[operation] = []
        self._samples[operation].extend(samples)
        # Invalidate cache
        self._cache.pop(operation, None)

    def calculate(self, operation: str) -> Optional[BaselineResult]:
        """Calculate the performance baseline (mean and stddev) for an operation."""
        if operation in self._cache:
            return self._cache[operation]
        samples = self._samples.get(operation)
        if not samples:
            return None
        mean = statistics.mean(samples)
        stddev = statistics.pstdev(samples) if len(samples) > 1 else 0.0
        result = BaselineResult(mean=mean, stddev=stddev)
        self._cache[operation] = result
        return result

    def recalculate(self, operation: str) -> Optional[BaselineResult]:
        """Force recalculation of the baseline by clearing the cache."""
        self._cache.pop(operation, None)
        return self.calculate(operation)

    @staticmethod
    def _remove_outliers(samples: List[float]) -> List[float]:
        if len(samples) < 3:
            return samples
        mean = statistics.mean(samples)
        stddev = statistics.pstdev(samples)
        if stddev == 0:
            return samples
        return [s for s in samples if abs(s - mean) <= 2 * stddev]


class AnomalyDetector:
    """Detects performance anomalies by comparing values against established baselines."""

    def __init__(self, threshold_stddev: float = 2.0):
        self.threshold_stddev = threshold_stddev
        self._baselines: Dict[str, Tuple[float, float]] = {}
        self._debounce_enabled = False
        self._min_occurrences = 1
        self._occurrence_counts: Dict[str, int] = {}

    def set_baseline(self, operation: str, mean: float, stddev: float):
        """Set the expected baseline for an operation used in anomaly detection."""
        self._baselines[operation] = (mean, stddev)
        self._occurrence_counts[operation] = 0

    def enable_debounce(self, min_occurrences: int):
        """Enable debouncing so alerts are suppressed until min_occurrences anomalies are seen."""
        self._debounce_enabled = True
        self._min_occurrences = min_occurrences

    def check(self, operation: str, value: float) -> AnomalyResult:
        """Check a value against the baseline and return an anomaly result."""
        baseline = self._baselines.get(operation)
        if baseline is None:
            return AnomalyResult(is_anomaly=False)

        mean, stddev = baseline
        if stddev == 0:
            return AnomalyResult(is_anomaly=False)

        deviation = (value - mean) / stddev
        is_anomaly = abs(deviation) > self.threshold_stddev

        if not is_anomaly:
            return AnomalyResult(is_anomaly=False, deviation=deviation)

        self._occurrence_counts[operation] = self._occurrence_counts.get(operation, 0) + 1

        alert_suppressed = False
        if self._debounce_enabled and self._occurrence_counts[operation] < self._min_occurrences:
            alert_suppressed = True

        severity = "critical" if abs(deviation) > self.threshold_stddev * 2 else "warning"
        alert = None if alert_suppressed else AnomalyAlert(severity=severity)

        return AnomalyResult(
            is_anomaly=True,
            deviation=deviation,
            alert=alert,
            alert_suppressed=alert_suppressed,
        )


_METRIC_RULES = {
    "upload_time": {
        "threshold": 3000,
        "unit": "ms",
        "description": "Reduce upload payload size or increase bandwidth allocation",
        "base_priority": 7,
    },
    "cpu_usage": {
        "threshold": 90.0,
        "unit": "percent",
        "description": "High CPU usage detected — consider reducing concurrent tasks or upgrading hardware",
        "base_priority": 9,
    },
    "disk_usage": {
        "threshold": 50.0,
        "unit": "percent",
        "description": "High disk usage — schedule storage cleanup or expand disk capacity",
        "base_priority": 8,
    },
}


class OptimizationAdvisor:
    """Generates prioritized optimization suggestions based on metric thresholds."""

    def __init__(self):
        self._metrics: List[Tuple[str, float, str]] = []

    def report_metric(self, name: str, value: float, unit: str):
        """Report a metric value for optimization analysis."""
        self._metrics.append((name, value, unit))

    def get_suggestions(self) -> List[Suggestion]:
        """Return prioritized optimization suggestions based on reported metrics."""
        suggestions: List[Suggestion] = []
        for name, value, unit in self._metrics:
            rule = _METRIC_RULES.get(name)
            if rule and value >= rule["threshold"]:
                excess = (value - rule["threshold"]) / rule["threshold"]
                priority = rule["base_priority"] + int(excess * 3)
                suggestions.append(Suggestion(description=rule["description"], priority=priority))
        suggestions.sort(key=lambda s: s.priority, reverse=True)
        return suggestions


class CapacityPlanner:
    """Projects resource usage trends and generates capacity alerts using linear regression."""

    def __init__(self):
        self._usage: Dict[str, List[Tuple[int, float]]] = {}
        self._capacity: Dict[str, float] = {}

    def add_usage_data(self, metric: str, data: List[Tuple[int, float]]):
        """Add historical usage data points as (week_number, value) tuples."""
        self._usage[metric] = data

    def set_capacity(self, metric: str, max_value: float):
        """Set the maximum capacity for a metric used in capacity alerts."""
        self._capacity[metric] = max_value

    def project(self, metric: str, weeks_ahead: int) -> Optional[Projection]:
        """Project a metric's value N weeks into the future using linear regression."""
        data = self._usage.get(metric)
        if not data or len(data) < 2:
            return None
        slope, intercept = self._linear_fit(data)
        last_week = data[-1][0]
        projected = slope * (last_week + weeks_ahead) + intercept
        return Projection(projected_value=projected)

    def analyze_trend(self, metric: str) -> Optional[Trend]:
        """Analyze the growth trend of a metric (increasing, decreasing, or stable)."""
        data = self._usage.get(metric)
        if not data or len(data) < 2:
            return None
        slope, _ = self._linear_fit(data)
        if slope > 0:
            direction = "increasing"
        elif slope < 0:
            direction = "decreasing"
        else:
            direction = "stable"
        return Trend(direction=direction, growth_rate=slope)

    def check_capacity(self, metric: str) -> Optional[CapacityAlert]:
        """Check if a metric is trending toward its capacity limit and return an alert."""
        max_val = self._capacity.get(metric)
        data = self._usage.get(metric)
        if max_val is None or not data or len(data) < 2:
            return None
        slope, intercept = self._linear_fit(data)
        if slope <= 0:
            return None
        last_week = data[-1][0]
        current_val = data[-1][1]
        weeks_until_full = (max_val - current_val) / slope
        severity = "critical" if weeks_until_full <= 4 else "warning"
        return CapacityAlert(weeks_until_full=weeks_until_full, severity=severity)

    @staticmethod
    def _linear_fit(data: List[Tuple[int, float]]) -> Tuple[float, float]:
        n = len(data)
        sum_x = sum(d[0] for d in data)
        sum_y = sum(d[1] for d in data)
        sum_xy = sum(d[0] * d[1] for d in data)
        sum_x2 = sum(d[0] ** 2 for d in data)
        denom = n * sum_x2 - sum_x ** 2
        if denom == 0:
            return 0.0, sum_y / n
        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n
        return slope, intercept


class PerformanceMonitor:
    """Orchestrator for performance monitoring subsystem."""

    def __init__(self):
        self.baseline = BaselineCalculator()
        self.anomaly_detector = AnomalyDetector()
        self.advisor = OptimizationAdvisor()
        self.planner = CapacityPlanner()
