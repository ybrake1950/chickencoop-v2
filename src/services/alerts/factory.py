"""Factory for creating alert instances."""


class Alert:
    """Base alert class."""

    def __init__(self, alert_type: str, severity: str = "medium", **kwargs):
        """Initialize an alert.

        Args:
            alert_type: Type identifier for this alert.
            severity: Alert severity level (default: 'medium').
            **kwargs: Additional alert-specific attributes.
        """
        self.alert_type = alert_type
        self.severity = severity
        for key, value in kwargs.items():
            setattr(self, key, value)


class TemperatureAlert(Alert):
    """Temperature-related alert."""

    def __init__(self, **kwargs):
        """Initialize a temperature alert.

        Args:
            **kwargs: Alert attributes (severity, threshold, temperature, etc.).
        """
        super().__init__(alert_type="temperature", **kwargs)


class MotionAlert(Alert):
    """Motion detection alert."""

    def __init__(self, **kwargs):
        """Initialize a motion detection alert.

        Args:
            **kwargs: Alert attributes (severity, camera, coop_id, etc.).
        """
        super().__init__(alert_type="motion", **kwargs)


class AlertFactory:
    """Factory for creating alert instances by type."""

    def create(self, alert_type: str, **kwargs):
        """Create an alert instance by type.

        Args:
            alert_type: Type of alert ('temperature', 'motion').

        Returns:
            Alert instance.
        """
        if alert_type == "temperature":
            return TemperatureAlert(**kwargs)
        elif alert_type == "motion":
            return MotionAlert(**kwargs)
        else:
            return Alert(alert_type=alert_type, **kwargs)
