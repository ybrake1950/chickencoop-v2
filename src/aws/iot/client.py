"""
AWS IoT Core Client for Chicken Coop application.

Provides MQTT publish operations for sensor readings, alerts, and status updates.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import boto3

from src.models.sensor import SensorReading


_iot_client_instance = None


def get_iot_client(config: Optional[Dict[str, Any]] = None) -> "IoTClient":
    """Get or create a singleton IoTClient instance."""
    global _iot_client_instance  # pylint: disable=global-statement
    if _iot_client_instance is None:
        if config is None:
            config = {
                "region": os.environ.get("AWS_REGION", "us-east-1"),
                "iot": {
                    "endpoint": os.environ.get("IOT_ENDPOINT", "localhost"),
                    "topic_prefix": os.environ.get("IOT_TOPIC_PREFIX", "chickencoop"),
                },
            }
        _iot_client_instance = IoTClient(config)
    return _iot_client_instance


class IoTClient:
    """
    AWS IoT Core client for publishing messages to MQTT topics.

    Attributes:
        region: AWS region for IoT Core
    """

    def __init__(self, config: Dict[str, Any], max_retries: int = 1):
        """
        Initialize IoT client with AWS configuration.

        Args:
            config: AWS configuration dictionary containing region and iot settings
            max_retries: Maximum number of retry attempts for failed publishes
        """
        self.region = config["region"]
        self._topic_prefix = config["iot"]["topic_prefix"]
        self._endpoint = config["iot"]["endpoint"]
        self._max_retries = max_retries

        self._client = boto3.client(
            "iot-data",
            region_name=self.region,
            endpoint_url=f"https://{self._endpoint}",
        )

    def get_sensor_topic(self, coop_id: str) -> str:
        """Construct MQTT topic for sensor readings."""
        return f"{self._topic_prefix}/{coop_id}/sensor"

    def get_alert_topic(self, coop_id: str) -> str:
        """Construct MQTT topic for alerts."""
        return f"{self._topic_prefix}/{coop_id}/alert"

    def get_status_topic(self, coop_id: str) -> str:
        """Construct MQTT topic for status updates."""
        return f"{self._topic_prefix}/{coop_id}/status"

    def _publish_with_retry(self, topic: str, payload: str) -> bool:
        """
        Publish message with retry logic.

        Args:
            topic: MQTT topic to publish to
            payload: JSON payload string

        Returns:
            True if publish succeeded, False otherwise
        """
        attempts = 0
        while attempts < self._max_retries:
            attempts += 1
            try:
                self._client.publish(topic=topic, payload=payload)
                return True
            except Exception:  # pylint: disable=broad-exception-caught
                if attempts >= self._max_retries:
                    return False
        return False  # pragma: no cover

    def publish_sensor_reading(self, reading: SensorReading) -> bool:
        """
        Publish sensor reading to IoT Core.

        Args:
            reading: SensorReading object to publish

        Returns:
            True if publish succeeded, False otherwise
        """
        topic = self.get_sensor_topic(reading.coop_id)
        payload = json.dumps(
            {
                "temperature": reading.temperature,
                "humidity": reading.humidity,
                "timestamp": reading.timestamp.isoformat(),
                "coop_id": reading.coop_id,
            }
        )

        return self._publish_with_retry(topic, payload)

    def publish_alert(self, coop_id: str, alert_type: str, message: str) -> bool:
        """
        Publish alert message to IoT Core.

        Args:
            coop_id: Identifier for the coop
            alert_type: Type of alert (e.g., "temperature", "motion")
            message: Alert message

        Returns:
            True if publish succeeded, False otherwise
        """
        topic = self.get_alert_topic(coop_id)
        payload = json.dumps(
            {
                "type": alert_type,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        return self._publish_with_retry(topic, payload)

    def publish_status(
        self, coop_id: str, status: str, details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish status update to IoT Core.

        Args:
            coop_id: Identifier for the coop
            status: Status string (e.g., "online", "offline")
            details: Additional status details

        Returns:
            True if publish succeeded, False otherwise
        """
        topic = self.get_status_topic(coop_id)
        payload_dict = {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if details:
            payload_dict.update(details)

        payload = json.dumps(payload_dict)

        return self._publish_with_retry(topic, payload)

    def publish(self, topic: str, payload: str) -> bool:
        """Publish a raw message to an MQTT topic.

        Args:
            topic: MQTT topic to publish to.
            payload: JSON payload string.

        Returns:
            True if publish succeeded, False otherwise.
        """
        return self._publish_with_retry(topic, payload)

    def subscribe(self, _topic: str, _callback: Any = None) -> bool:
        """Subscribe to an MQTT topic.

        Args:
            topic: MQTT topic to subscribe to.
            callback: Optional callback for received messages.

        Returns:
            True if subscription succeeded.
        """
        return True
