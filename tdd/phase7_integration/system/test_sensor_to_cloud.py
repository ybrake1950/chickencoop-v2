"""
TDD Tests: Sensor to Cloud Integration

These tests verify the complete flow from sensor reading to cloud storage.
These are integration tests that test multiple components together.

Run: pytest tdd/phase7_integration/system/test_sensor_to_cloud.py -v
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone


# =============================================================================
# Test: Sensor Reading → Local Storage
# =============================================================================

class TestSensorToLocalStorage:
    """Tests for sensor data flow to local storage."""

    def test_sensor_reading_saved_to_csv(self, tmp_path, sample_sensor_reading):
        """Sensor reading should be saved to CSV file."""
        from src.hardware.sensors.monitor import SensorMonitor
        from src.persistence.csv_storage import CSVStorage

        csv_path = tmp_path / "sensor_data.csv"
        storage = CSVStorage(csv_path)
        monitor = SensorMonitor()

        # Mock sensor
        mock_sensor = MagicMock()
        mock_sensor.name = "combined"
        mock_sensor.read.return_value = {
            "temperature": 72.5,
            "humidity": 65.0
        }
        monitor.register_sensor(mock_sensor)

        # Read and store
        readings = monitor.read_all()
        storage.append_reading(readings, coop_id="test")

        # Verify
        assert csv_path.exists()
        content = csv_path.read_text()
        assert "72.5" in content
        assert "65.0" in content

    def test_sensor_reading_saved_to_database(self, test_db_path, sample_sensor_reading):
        """Sensor reading should be saved to database."""
        from src.persistence.database import Database
        from src.persistence.repositories.sensor import SensorRepository
        from src.models.sensor import SensorReading

        db = Database(test_db_path)
        db.create_tables()
        repo = SensorRepository(db)

        reading = SensorReading(
            temperature=sample_sensor_reading["temperature"],
            humidity=sample_sensor_reading["humidity"],
            coop_id=sample_sensor_reading["coop_id"]
        )

        reading_id = repo.save(reading)

        assert reading_id is not None

        # Verify retrieval
        saved = repo.get_latest()
        assert saved.temperature == 72.5


# =============================================================================
# Test: Sensor Reading → AWS IoT
# =============================================================================

class TestSensorToAWSIoT:
    """Tests for sensor data flow to AWS IoT."""

    def test_sensor_reading_published_to_iot(self, sample_aws_config, mock_iot_client):
        """Sensor reading should be published to IoT Core."""
        from src.aws.iot.client import IoTClient
        from src.models.sensor import SensorReading

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)

            reading = SensorReading(
                temperature=72.5,
                humidity=65.0,
                coop_id="test"
            )

            result = client.publish_sensor_reading(reading)

        assert result is True
        mock_iot_client.publish.assert_called_once()

    def test_iot_message_format(self, sample_aws_config, mock_iot_client):
        """IoT message should have correct format."""
        from src.aws.iot.client import IoTClient
        from src.models.sensor import SensorReading
        import json

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)

            reading = SensorReading(
                temperature=72.5,
                humidity=65.0,
                coop_id="coop1"
            )

            client.publish_sensor_reading(reading)

        # Get the published payload
        call_args = mock_iot_client.publish.call_args
        payload = json.loads(call_args.kwargs.get('payload', call_args[1].get('payload', '{}')))

        assert "temperature" in payload
        assert "humidity" in payload
        assert "timestamp" in payload

    def test_iot_topic_includes_coop_id(self, sample_aws_config, mock_iot_client):
        """IoT topic should include coop ID."""
        from src.aws.iot.client import IoTClient
        from src.models.sensor import SensorReading

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)

            reading = SensorReading(
                temperature=72.5,
                humidity=65.0,
                coop_id="coop1"
            )

            client.publish_sensor_reading(reading)

        call_args = mock_iot_client.publish.call_args
        topic = call_args.kwargs.get('topic', call_args[1].get('topic', ''))

        assert "coop1" in topic


# =============================================================================
# Test: Sensor Reading → S3
# =============================================================================

class TestSensorToS3:
    """Tests for sensor data flow to S3."""

    def test_csv_backup_uploaded_to_s3(self, tmp_path, sample_aws_config, mock_s3_client):
        """Daily CSV should be backed up to S3."""
        from src.aws.s3.client import S3Client
        from src.persistence.csv_storage import CSVStorage

        # Create CSV with data
        csv_path = tmp_path / "sensor_data_20250125.csv"
        csv_path.write_text("timestamp,temperature,humidity,coop_id\n2025-01-25 14:30:00,72.5,65.0,test\n")

        with patch('boto3.client', return_value=mock_s3_client):
            s3_client = S3Client(sample_aws_config)
            result = s3_client.upload_file(csv_path, "csv/sensor_data_20250125.csv")

        assert result is True
        mock_s3_client.upload_file.assert_called_once()


# =============================================================================
# Test: Alert Generation
# =============================================================================

class TestSensorAlertGeneration:
    """Tests for alert generation from sensor readings."""

    def test_high_temperature_triggers_alert(self, sample_aws_config, mock_sns_client):
        """High temperature should trigger SNS alert."""
        from src.aws.sns.client import SNSClient
        from src.models.sensor import SensorReading
        from src.services.alert_service import AlertService

        with patch('boto3.client', return_value=mock_sns_client):
            sns_client = SNSClient(sample_aws_config)
            alert_service = AlertService(
                sns_client=sns_client,
                temp_max=90
            )

            reading = SensorReading(
                temperature=95.0,  # Above threshold
                humidity=65.0,
                coop_id="test"
            )

            alert_service.check_and_alert(reading)

        mock_sns_client.publish.assert_called_once()

    def test_normal_temperature_no_alert(self, sample_aws_config, mock_sns_client):
        """Normal temperature should not trigger alert."""
        from src.aws.sns.client import SNSClient
        from src.models.sensor import SensorReading
        from src.services.alert_service import AlertService

        with patch('boto3.client', return_value=mock_sns_client):
            sns_client = SNSClient(sample_aws_config)
            alert_service = AlertService(
                sns_client=sns_client,
                temp_max=90
            )

            reading = SensorReading(
                temperature=72.5,  # Normal
                humidity=65.0,
                coop_id="test"
            )

            alert_service.check_and_alert(reading)

        mock_sns_client.publish.assert_not_called()


# =============================================================================
# Test: Full Pipeline
# =============================================================================

class TestFullSensorPipeline:
    """Tests for the complete sensor data pipeline."""

    def test_complete_sensor_pipeline(
        self,
        tmp_path,
        test_db_path,
        sample_aws_config,
        mock_s3_client,
        mock_iot_client,
        mock_sns_client
    ):
        """Test complete flow: Read → Store → Upload → Alert."""
        from src.hardware.sensors.monitor import SensorMonitor
        from src.persistence.database import Database
        from src.persistence.csv_storage import CSVStorage
        from src.aws.s3.client import S3Client
        from src.aws.iot.client import IoTClient
        from src.services.sensor_service import SensorService

        # Setup components
        with patch('boto3.client') as mock_boto:
            mock_boto.side_effect = lambda service, **kwargs: {
                's3': mock_s3_client,
                'iot-data': mock_iot_client,
                'sns': mock_sns_client
            }.get(service, MagicMock())

            db = Database(test_db_path)
            db.create_tables()

            csv_storage = CSVStorage(tmp_path / "sensor_data.csv")
            s3_client = S3Client(sample_aws_config)
            iot_client = IoTClient(sample_aws_config)

            service = SensorService(
                database=db,
                csv_storage=csv_storage,
                s3_client=s3_client,
                iot_client=iot_client,
                coop_id="test"
            )

            # Mock sensor reading
            mock_sensor = MagicMock()
            mock_sensor.name = "combined"
            mock_sensor.read.return_value = {
                "temperature": 72.5,
                "humidity": 65.0
            }

            # Execute pipeline
            result = service.process_reading(mock_sensor.read())

        # Verify all stages completed
        assert result["stored_locally"] is True
        assert result["published_iot"] is True
