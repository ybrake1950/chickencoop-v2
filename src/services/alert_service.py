"""
Alert service for monitoring sensor readings and triggering alerts.
"""

from typing import Optional

from src.aws.sns.client import SNSClient
from src.models.sensor import SensorReading


class AlertService:
    """Service for checking sensor readings and triggering alerts."""

    def __init__(
        self,
        sns_client: SNSClient,
        temp_max: float = 90.0,
        temp_min: Optional[float] = None,
        humidity_max: Optional[float] = None,
        humidity_min: Optional[float] = None
    ):
        """Initialize alert service with thresholds.

        Args:
            sns_client: SNS client for sending alerts.
            temp_max: Maximum temperature threshold.
            temp_min: Minimum temperature threshold.
            humidity_max: Maximum humidity threshold.
            humidity_min: Minimum humidity threshold.
        """
        self._sns_client = sns_client
        self._temp_max = temp_max
        self._temp_min = temp_min
        self._humidity_max = humidity_max
        self._humidity_min = humidity_min

    def check_and_alert(self, reading: SensorReading) -> bool:
        """Check reading against thresholds and send alerts if needed.

        Args:
            reading: SensorReading to check.

        Returns:
            True if an alert was sent, False otherwise.
        """
        alert_sent = False

        if self._temp_max is not None and reading.temperature > self._temp_max:
            self._sns_client.publish_temperature_alert(
                coop_id=reading.coop_id,
                temperature=reading.temperature,
                threshold=self._temp_max
            )
            alert_sent = True

        if self._temp_min is not None and reading.temperature < self._temp_min:
            self._sns_client.publish_temperature_alert(
                coop_id=reading.coop_id,
                temperature=reading.temperature,
                threshold=self._temp_min
            )
            alert_sent = True

        return alert_sent

    def send_alert(self, subject: str, message: str):
        """Send an alert notification.

        Args:
            subject: Alert subject.
            message: Alert message body.
        """
        return self._sns_client.publish_alert(subject, message)
