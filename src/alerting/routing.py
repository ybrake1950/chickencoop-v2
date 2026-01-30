"""
Alert routing module for the chicken coop application.

Routes alerts to appropriate channels based on alert type, severity,
time-based rules, and per-user preferences.
"""

from dataclasses import dataclass, field
from datetime import time
from enum import Enum
from typing import List, Optional


class AlertChannel(Enum):
    """Notification channels for alerts."""
    SNS = "sns"
    SLACK = "slack"
    EMAIL = "email"
    LOG = "log"


@dataclass
class RoutingRule:
    """A rule mapping an alert type to channels."""
    alert_type: str
    channels: List[AlertChannel] = field(default_factory=list)


@dataclass
class RoutingConfig:
    """Configuration for the alert router."""
    rules: List[RoutingRule] = field(default_factory=list)


@dataclass
class UserPreferences:
    """Per-user routing preferences."""
    channels: List[AlertChannel] = field(default_factory=list)
    alert_types: List[str] = field(default_factory=list)
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None


@dataclass
class RouteResult:
    """Result of routing an alert."""
    channels: List[AlertChannel] = field(default_factory=list)
    queued: bool = False
    suppressed: bool = False


class AlertRouter:
    """Routes alerts to appropriate notification channels."""

    def __init__(self, config: Optional[RoutingConfig] = None):
        self._config = config or RoutingConfig()
        self._rules = {rule.alert_type: rule for rule in self._config.rules}
        self._severity_channels: dict[str, List[AlertChannel]] = {}
        self._quiet_hours_start: Optional[time] = None
        self._quiet_hours_end: Optional[time] = None
        self._quiet_hours_timezone: Optional[str] = None
        self._user_preferences: dict[str, UserPreferences] = {}

    @property
    def quiet_hours_start(self) -> Optional[time]:
        return self._quiet_hours_start

    @property
    def quiet_hours_end(self) -> Optional[time]:
        return self._quiet_hours_end

    @property
    def quiet_hours_timezone(self) -> Optional[str]:
        return self._quiet_hours_timezone

    def add_rule(self, rule: RoutingRule) -> None:
        """Add a routing rule."""
        self._rules[rule.alert_type] = rule

    def get_channels(
        self,
        alert_type: str,
        severity: Optional[str] = None,
        current_time: Optional[time] = None,
    ) -> List[AlertChannel]:
        """Get the channels for an alert based on type, severity, and time."""
        rule = self._rules.get(alert_type)
        if not rule:
            return []

        channels = list(rule.channels)

        if severity == "info":
            return [AlertChannel.LOG]

        if severity == "warning":
            # Use a subset: first channel only
            channels = channels[:1] if channels else []

        if current_time is not None and self._is_quiet_hours(current_time):
            if severity != "critical":
                return [AlertChannel.LOG]

        return channels

    def set_severity_channels(self, severity: str, channels: List[AlertChannel]) -> None:
        """Configure channels for a severity level."""
        self._severity_channels[severity] = channels

    def get_severity_channels(self, severity: str) -> List[AlertChannel]:
        """Get configured channels for a severity level."""
        return self._severity_channels.get(severity, [])

    def set_quiet_hours(
        self,
        start: time,
        end: time,
        timezone: Optional[str] = None,
    ) -> None:
        """Set quiet hours during which non-critical alerts are suppressed."""
        self._quiet_hours_start = start
        self._quiet_hours_end = end
        self._quiet_hours_timezone = timezone

    def _is_quiet_hours(self, current_time: time) -> bool:
        """Check if the given time falls within quiet hours."""
        if self._quiet_hours_start is None or self._quiet_hours_end is None:
            return False

        start = self._quiet_hours_start
        end = self._quiet_hours_end

        if start <= end:
            return start <= current_time <= end
        else:
            # Overnight quiet hours (e.g., 22:00 - 07:00)
            return current_time >= start or current_time <= end

    def route_alert(
        self,
        alert_type: str,
        severity: Optional[str] = None,
        current_time: Optional[time] = None,
    ) -> RouteResult:
        """Route an alert and return the result."""
        channels = self.get_channels(alert_type, severity, current_time)

        if current_time is not None and self._is_quiet_hours(current_time) and severity != "critical":
            return RouteResult(channels=[], queued=True, suppressed=True)

        return RouteResult(channels=channels)

    def set_user_preference(
        self,
        user_id: str,
        preferred_channels: Optional[List[AlertChannel]] = None,
        alert_types: Optional[List[str]] = None,
        quiet_hours_start: Optional[time] = None,
        quiet_hours_end: Optional[time] = None,
    ) -> None:
        """Set routing preferences for a user."""
        prefs = self._user_preferences.get(user_id, UserPreferences())

        if preferred_channels is not None:
            prefs.channels = preferred_channels
        if alert_types is not None:
            prefs.alert_types = alert_types
        if quiet_hours_start is not None:
            prefs.quiet_hours_start = quiet_hours_start
        if quiet_hours_end is not None:
            prefs.quiet_hours_end = quiet_hours_end

        self._user_preferences[user_id] = prefs

    def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get routing preferences for a user."""
        return self._user_preferences.get(user_id, UserPreferences())
