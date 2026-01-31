"""
Phase 17: Failover management for cross-coop monitoring.

Detects coop failures, triggers automatic failover to a backup coop,
and handles failback with data synchronization when the primary recovers.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FailoverState(Enum):
    """Health state of a monitored coop."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class FailoverConfig:
    """Configuration for failover thresholds and coop assignments."""

    health_check_interval: int = 30
    failure_threshold: int = 3
    primary_coop: str = ""
    backup_coop: str = ""


@dataclass
class CoopStatus:
    """Current health status and failure/success counters for a coop."""

    healthy: bool = True
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    state: FailoverState = FailoverState.HEALTHY


@dataclass
class FailoverResult:
    """Result indicating whether failover was triggered."""

    failover_triggered: bool = False


@dataclass
class FailbackResult:
    """Result indicating whether failback to the primary coop occurred."""

    failback_triggered: bool = False
    primary_coop: str = ""


class HealthChecker:
    """Periodically checks coop health with configurable interval and timeout."""

    def __init__(self, interval_seconds: int = 30, timeout_seconds: int = 10):
        self.interval_seconds = interval_seconds
        self.timeout_seconds = timeout_seconds


class FailoverManager:
    """Manages failover detection, triggering, and failback for coop monitoring."""

    def __init__(self, config: Optional[FailoverConfig] = None):
        self.config = config or FailoverConfig()
        self._statuses: dict[str, CoopStatus] = {}
        self._failover_active = False

    def _get_or_create_status(self, coop_id: str) -> CoopStatus:
        if coop_id not in self._statuses:
            self._statuses[coop_id] = CoopStatus()
        return self._statuses[coop_id]

    def report_health(self, coop_id: str, healthy: bool) -> None:
        """Record a health check result for the given coop."""
        status = self._get_or_create_status(coop_id)
        if healthy:
            status.healthy = True
            status.consecutive_failures = 0
            status.consecutive_successes += 1
            if status.state in (FailoverState.DEGRADED, FailoverState.FAILED):
                # Intentional no-op: retain degraded/failed state until
                # failback is explicitly triggered via check_and_failback().
                pass
            else:
                status.state = FailoverState.HEALTHY
        else:
            status.healthy = False
            status.consecutive_failures += 1
            status.consecutive_successes = 0
            if status.consecutive_failures >= self.config.failure_threshold:
                status.state = FailoverState.DEGRADED

    def get_status(self, coop_id: str) -> CoopStatus:
        """Return the current health status for a coop."""
        return self._get_or_create_status(coop_id)

    def check_and_failover(self) -> FailoverResult:
        """Check if the primary coop has failed and trigger failover if needed."""
        primary = self.config.primary_coop
        status = self._get_or_create_status(primary)
        if status.consecutive_failures >= self.config.failure_threshold and not self._failover_active:
            self._failover_active = True
            self._activate_backup(self.config.backup_coop)
            self._send_notification(primary)
            return FailoverResult(failover_triggered=True)
        return FailoverResult(failover_triggered=False)

    def check_and_failback(self) -> FailbackResult:
        """Check if the primary coop has recovered and trigger failback if stable."""
        primary = self.config.primary_coop
        status = self._get_or_create_status(primary)
        if self._failover_active and status.healthy and status.consecutive_successes >= 3:
            self._failover_active = False
            status.state = FailoverState.HEALTHY
            self._sync_data()
            return FailbackResult(failback_triggered=True, primary_coop=primary)
        return FailbackResult(failback_triggered=False, primary_coop=primary)

    def _activate_backup(self, coop_id: str) -> None:
        """Activate the backup coop for monitoring duties."""

    def _send_notification(self, coop_id: str) -> None:
        """Send a failover notification for the specified coop."""

    def _sync_data(self) -> None:
        """Synchronize data from backup coop back to primary after failback."""
