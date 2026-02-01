"""Alert aggregation: debouncing, digests, cooldowns, trends, and predictions."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class DebounceSummary:
    """Summary of suppressed alerts after debounce window."""

    suppressed_count: int


@dataclass
class AlertDigest:
    """Digest summary of accumulated alerts."""

    total_alerts: int
    counts_by_type: Dict[str, int]
    max_value: Optional[float]
    min_value: Optional[float]


@dataclass
class CooldownResult:
    """Result of a cooldown check."""

    can_send: bool


@dataclass
class TrendResult:
    """Result of trend detection."""

    direction: str
    rate_per_hour: float


@dataclass
class PredictionResult:
    """Result of a predictive breach analysis."""

    will_breach: bool
    estimated_time: Optional[datetime]
    minutes_until_breach: float
    confidence: float


class AlertDebouncer:
    """Debounces rapid repeated alerts within a configurable time window."""

    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self._last_sent: Dict[str, datetime] = {}
        self._suppressed: Dict[str, int] = {}

    def should_send(self, alert_type: str, timestamp: datetime) -> bool:
        """Check if an alert should be sent or suppressed due to debouncing."""
        last = self._last_sent.get(alert_type)
        if last is None or (timestamp - last).total_seconds() >= self.window_seconds:
            self._last_sent[alert_type] = timestamp
            self._suppressed[alert_type] = 0
            return True
        self._suppressed[alert_type] = self._suppressed.get(alert_type, 0) + 1
        return False

    def get_summary(
        self, alert_type: str, timestamp: datetime
    ) -> Optional[DebounceSummary]:
        """Return a summary of suppressed alerts if the debounce window has elapsed."""
        last = self._last_sent.get(alert_type)
        if last is None:
            return None
        if (timestamp - last).total_seconds() >= self.window_seconds:
            count = self._suppressed.get(alert_type, 0)
            if count > 0:
                summary = DebounceSummary(suppressed_count=count)
                self._suppressed[alert_type] = 0
                self._last_sent[alert_type] = timestamp
                return summary
        return None


class AlertAggregator:
    """Aggregates alerts for digests and manages cooldowns."""

    def __init__(self):
        self._alerts: List[Dict[str, Any]] = []
        self._cooldowns: Dict[str, int] = {}
        self._last_sent: Dict[str, datetime] = {}
        self._resolved: set = set()
        self.digest_hour: int = 8
        self.digest_minute: int = 0

    def add_alert(self, alert: Dict[str, Any]) -> None:
        """Add an alert to the aggregation buffer for digest generation."""
        self._alerts.append(alert)

    def generate_digest(  # pylint: disable=unused-argument
        self, period: str = "daily"
    ) -> Optional[AlertDigest]:
        """Generate a digest summarizing all accumulated alerts with counts and extremes."""
        if not self._alerts:
            return AlertDigest(
                total_alerts=0, counts_by_type={}, max_value=None, min_value=None
            )

        counts: Dict[str, int] = {}
        values: List[float] = []
        for a in self._alerts:
            t = a.get("type", "unknown")
            counts[t] = counts.get(t, 0) + 1
            if "value" in a:
                values.append(a["value"])

        return AlertDigest(
            total_alerts=len(self._alerts),
            counts_by_type=counts,
            max_value=max(values) if values else None,
            min_value=min(values) if values else None,
        )

    def set_digest_schedule(self, hour: int, minute: int) -> None:
        """Configure the time of day for digest delivery."""
        self.digest_hour = hour
        self.digest_minute = minute

    def set_cooldown(self, alert_type: str, seconds: int) -> None:
        """Set the cooldown duration in seconds for a specific alert type."""
        self._cooldowns[alert_type] = seconds

    def get_cooldown(self, alert_type: str) -> int:
        """Return the cooldown duration in seconds for the given alert type."""
        return self._cooldowns.get(alert_type, 0)

    def mark_sent(self, alert_type: str, timestamp: datetime) -> None:
        """Record that an alert was sent, starting the cooldown timer."""
        self._last_sent[alert_type] = timestamp
        self._resolved.discard(alert_type)

    def mark_resolved(self, alert_type: str) -> None:
        """Mark an alert type as resolved, resetting its cooldown."""
        self._resolved.add(alert_type)
        self._last_sent.pop(alert_type, None)

    def check_cooldown(
        self, alert_type: str, timestamp: datetime, severity: Optional[str] = None
    ) -> CooldownResult:
        """Check whether an alert can be sent or is blocked by a cooldown period."""
        if severity == "critical":
            return CooldownResult(can_send=True)

        if alert_type in self._resolved:
            return CooldownResult(can_send=True)

        last = self._last_sent.get(alert_type)
        if last is None:
            return CooldownResult(can_send=True)

        cooldown = self._cooldowns.get(alert_type, 0)
        if (timestamp - last).total_seconds() >= cooldown:
            return CooldownResult(can_send=True)

        return CooldownResult(can_send=False)


class TrendDetector:
    """Detects rising/falling trends in sensor readings."""

    def __init__(self, rate_threshold: float = 5.0, window_minutes: int = 30):
        self.rate_threshold = rate_threshold
        self.window_minutes = window_minutes
        self._readings: List[Dict[str, Any]] = []

    def add_reading(self, reading: Dict[str, Any]) -> None:
        """Add a sensor reading for trend analysis."""
        self._readings.append(reading)

    def detect_trend(self) -> Optional[TrendResult]:
        """Analyze readings for a rising or falling trend exceeding the rate threshold."""
        if len(self._readings) < 2:
            return None

        first = self._readings[0]
        last = self._readings[-1]

        t0 = datetime.fromisoformat(first["timestamp"])
        t1 = datetime.fromisoformat(last["timestamp"])
        hours = (t1 - t0).total_seconds() / 3600.0

        if hours == 0:
            return None

        rate = (last["value"] - first["value"]) / hours

        if abs(rate) >= self.rate_threshold:
            direction = "rising" if rate > 0 else "falling"
            return TrendResult(direction=direction, rate_per_hour=rate)

        return None


class PredictiveAlert:
    """Predicts future threshold breaches by extrapolating current trends."""

    def __init__(self, threshold: float = 100.0):
        self.threshold = threshold
        self._readings: List[Dict[str, Any]] = []

    def add_reading(self, reading: Dict[str, Any]) -> None:
        """Add a sensor reading for breach prediction."""
        self._readings.append(reading)

    def predict_breach(self) -> Optional[PredictionResult]:
        """Predict if and when the threshold will be breached based on current trend."""
        if len(self._readings) < 2:
            return None

        first = self._readings[0]
        last = self._readings[-1]

        t0 = datetime.fromisoformat(first["timestamp"])
        t1 = datetime.fromisoformat(last["timestamp"])
        minutes_elapsed = (t1 - t0).total_seconds() / 60.0

        if minutes_elapsed == 0:
            return None

        rate_per_min = (last["value"] - first["value"]) / minutes_elapsed

        if rate_per_min <= 0:
            return None

        remaining = self.threshold - last["value"]
        if remaining <= 0:
            return PredictionResult(
                will_breach=True,
                estimated_time=t1,
                minutes_until_breach=0.0,
                confidence=1.0,
            )

        minutes_until = remaining / rate_per_min
        estimated_time = t1 + timedelta(minutes=minutes_until)

        n = len(self._readings)
        confidence = min(1.0, n / 10.0)

        return PredictionResult(
            will_breach=True,
            estimated_time=estimated_time,
            minutes_until_breach=minutes_until,
            confidence=confidence,
        )
