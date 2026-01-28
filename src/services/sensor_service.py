"""
Sensor service for managing the complete sensor data pipeline.
"""

from typing import Any, Dict, Optional

from src.aws.iot.client import IoTClient
from src.aws.s3.client import S3Client
from src.models.sensor import SensorReading
from src.persistence.csv_storage import CSVStorage
from src.persistence.database import Database
from src.persistence.repositories.sensor import SensorRepository


class SensorService:
    """Service for processing sensor readings through the complete pipeline."""

    def __init__(
        self,
        database: Database,
        csv_storage: CSVStorage,
        s3_client: Optional[S3Client] = None,
        iot_client: Optional[IoTClient] = None,
        coop_id: str = "default"
    ):
        """Initialize sensor service with storage and cloud clients.

        Args:
            database: Database connection for local persistence.
            csv_storage: CSV storage for local file persistence.
            s3_client: S3 client for cloud backup.
            iot_client: IoT client for real-time publishing.
            coop_id: Default coop identifier.
        """
        self._database = database
        self._csv_storage = csv_storage
        self._s3_client = s3_client
        self._iot_client = iot_client
        self._coop_id = coop_id
        self._sensor_repo = SensorRepository(database)

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
            "backed_up_s3": False
        }

        temperature = readings.get("temperature", 0.0)
        humidity = readings.get("humidity", 0.0)

        reading = SensorReading(
            temperature=temperature,
            humidity=humidity,
            coop_id=self._coop_id
        )

        # Store to database
        try:
            self._sensor_repo.save(reading)
            result["stored_locally"] = True
        except Exception:
            pass

        # Store to CSV
        try:
            self._csv_storage.append_reading(readings, self._coop_id)
        except Exception:
            pass

        # Publish to IoT
        if self._iot_client:
            try:
                published = self._iot_client.publish_sensor_reading(reading)
                result["published_iot"] = published
            except Exception:
                pass

        return result
