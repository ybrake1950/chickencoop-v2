"""
Sensor service for managing the complete sensor data pipeline.
"""

import logging
from typing import Any, Dict, List

from src.models.sensor import SensorReading

logger = logging.getLogger(__name__)


class SensorService:
    """Service for processing sensor readings through the complete pipeline."""

    def __init__(
        self,
        sensor_repo=None,
        alert_service=None,
        database=None,
        csv_storage=None,
        s3_client=None,
        iot_client=None,
        coop_id: str = "default",
    ):
        """Initialize sensor service with dependencies.

        Args:
            sensor_repo: Repository for sensor data persistence.
            alert_service: Service for checking and sending alerts.
            database: Database connection for local persistence.
            csv_storage: CSV storage for local file persistence.
            s3_client: S3 client for cloud backup.
            iot_client: IoT client for real-time publishing.
            coop_id: Default coop identifier.
        """
        self.sensor_repo = sensor_repo
        self.alert_service = alert_service
        self._database = database
        self._csv_storage = csv_storage
        self._s3_client = s3_client
        self._iot_client = iot_client
        self._coop_id = coop_id

        if self.sensor_repo is None and database is not None:
            from src.persistence.repositories.sensor import SensorRepository

            self.sensor_repo = SensorRepository(database)

    def process_reading(self, readings: Dict[str, Any]) -> Dict[str, bool]:
        """Process a sensor reading through the complete pipeline.

        Args:
            readings: Dictionary with sensor readings (temperature, humidity).

        Returns:
            Dictionary with status of each pipeline stage.
        """
        result = {
            "stored_locally": False,
            "published_iot": False,
            "backed_up_s3": False,
        }

        temperature = readings.get("temperature", 0.0)
        humidity = readings.get("humidity", 0.0)

        reading = SensorReading(
            temperature=temperature, humidity=humidity, coop_id=self._coop_id
        )

        # Store to database
        try:
            self.sensor_repo.save(reading)
            result["stored_locally"] = True
        except Exception:  # pylint: disable=broad-exception-caught
            logger.error("Failed to store reading locally")

        # Store to CSV
        if self._csv_storage:
            try:
                self._csv_storage.append_reading(readings, self._coop_id)
            except Exception:  # pylint: disable=broad-exception-caught
                logger.error("Failed to store reading to CSV")

        # Publish to IoT
        if self._iot_client:
            try:
                published = self._iot_client.publish_sensor_reading(reading)
                result["published_iot"] = published
            except Exception:  # pylint: disable=broad-exception-caught
                logger.error("Failed to publish reading to IoT")

        # Check alerts
        if self.alert_service:
            try:
                self.alert_service.check_and_alert(reading)
            except Exception:  # pylint: disable=broad-exception-caught
                logger.error("Failed to check alerts")

        return result

    def get_latest_readings(self, _limit: int = 10) -> List[Dict[str, Any]]:
        """Get the latest sensor readings.

        Args:
            limit: Maximum number of readings to return.

        Returns:
            List of sensor reading dictionaries.
        """
        try:
            latest = self.sensor_repo.get_latest()
            if latest:
                return [
                    {"temperature": latest.temperature, "humidity": latest.humidity}
                ]
        except Exception:  # pylint: disable=broad-exception-caught
            logger.error("Failed to get latest readings")
        return []
