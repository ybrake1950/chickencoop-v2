"""
TDD Tests: AWS IoT Core Client

These tests define the expected behavior for IoT Core MQTT operations.
Implement src/aws/iot/client.py to make these tests pass.

Run: pytest tdd/phase4_aws/iot/test_iot_client.py -v

FUNCTIONALITY BEING TESTED:
- IoT client initialization with configuration
- Publishing sensor readings to MQTT topics
- Topic naming with coop ID prefix
- Message payload formatting (JSON)
- QoS (Quality of Service) configuration
- Connection state management
- Error handling for publish failures

WHY THIS MATTERS:
IoT Core provides real-time sensor data to the React dashboard. When a sensor
reading is taken, it's published to a topic like "chickencoop/coop1/sensors".
The dashboard subscribes to these topics for live updates.

HOW TESTS ARE EXECUTED:
1. Tests use mock_iot_client fixture (mocked boto3 iot-data client)
2. IoTClient class wraps the boto3 client
3. Publish operations are called and mock interactions verified
4. Topic names and payload structure are validated
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


# =============================================================================
# Test: IoT Client Initialization
# =============================================================================

class TestIoTClientInit:
    """Tests for IoT client initialization."""

    def test_client_initializes_with_config(self, sample_aws_config, mock_iot_client):
        """IoTClient should initialize with AWS configuration."""
        from src.aws.iot.client import IoTClient

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)

        assert client is not None

    def test_client_uses_configured_endpoint(self, sample_aws_config, mock_iot_client):
        """Client should use IoT endpoint from config."""
        from src.aws.iot.client import IoTClient

        with patch('boto3.client', return_value=mock_iot_client) as mock_boto:
            client = IoTClient(sample_aws_config)

        # Verify endpoint was used in client creation
        assert mock_boto.called

    def test_client_uses_configured_region(self, sample_aws_config, mock_iot_client):
        """Client should use AWS region from config."""
        from src.aws.iot.client import IoTClient

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)

        assert client.region == sample_aws_config["region"]


# =============================================================================
# Test: Publishing Sensor Readings
# =============================================================================

class TestPublishSensorReading:
    """Tests for publishing sensor readings to IoT Core."""

    def test_publish_returns_true_on_success(self, sample_aws_config, mock_iot_client):
        """Successful publish should return True."""
        from src.aws.iot.client import IoTClient
        from src.models.sensor import SensorReading

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)
            reading = SensorReading(
                temperature=72.5,
                humidity=65.0,
                coop_id="coop1"
            )

            result = client.publish_sensor_reading(reading)

        assert result is True

    def test_publish_calls_iot_publish(self, sample_aws_config, mock_iot_client):
        """Should call IoT Data publish method."""
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

        mock_iot_client.publish.assert_called_once()

    def test_publish_uses_correct_topic(self, sample_aws_config, mock_iot_client):
        """Topic should include coop ID and sensor type."""
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

        call_kwargs = mock_iot_client.publish.call_args.kwargs
        topic = call_kwargs.get('topic', '')

        assert "coop1" in topic
        assert "sensor" in topic.lower()

    def test_publish_payload_is_json(self, sample_aws_config, mock_iot_client):
        """Payload should be valid JSON."""
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

        call_kwargs = mock_iot_client.publish.call_args.kwargs
        payload = call_kwargs.get('payload', '{}')

        # Should be valid JSON
        parsed = json.loads(payload)
        assert isinstance(parsed, dict)

    def test_publish_payload_contains_reading_data(self, sample_aws_config, mock_iot_client):
        """Payload should contain temperature, humidity, timestamp."""
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

        call_kwargs = mock_iot_client.publish.call_args.kwargs
        payload = json.loads(call_kwargs.get('payload', '{}'))

        assert payload["temperature"] == 72.5
        assert payload["humidity"] == 65.0
        assert "timestamp" in payload
        assert payload["coop_id"] == "coop1"


# =============================================================================
# Test: Topic Management
# =============================================================================

class TestTopicManagement:
    """Tests for IoT topic construction."""

    def test_get_sensor_topic(self, sample_aws_config, mock_iot_client):
        """Should construct correct sensor topic."""
        from src.aws.iot.client import IoTClient

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)
            topic = client.get_sensor_topic("coop1")

        assert "coop1" in topic
        assert "sensor" in topic.lower()

    def test_get_alert_topic(self, sample_aws_config, mock_iot_client):
        """Should construct correct alert topic."""
        from src.aws.iot.client import IoTClient

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)
            topic = client.get_alert_topic("coop1")

        assert "coop1" in topic
        assert "alert" in topic.lower()

    def test_get_status_topic(self, sample_aws_config, mock_iot_client):
        """Should construct correct status topic."""
        from src.aws.iot.client import IoTClient

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)
            topic = client.get_status_topic("coop1")

        assert "coop1" in topic
        assert "status" in topic.lower()

    def test_topic_uses_config_prefix(self, sample_aws_config, mock_iot_client):
        """Topic should use prefix from config."""
        from src.aws.iot.client import IoTClient

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)
            topic = client.get_sensor_topic("coop1")

        prefix = sample_aws_config["iot"]["topic_prefix"]
        assert topic.startswith(prefix)


# =============================================================================
# Test: Publishing Alerts
# =============================================================================

class TestPublishAlert:
    """Tests for publishing alerts to IoT Core."""

    def test_publish_alert_success(self, sample_aws_config, mock_iot_client):
        """Should publish alert message."""
        from src.aws.iot.client import IoTClient

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)
            result = client.publish_alert(
                coop_id="coop1",
                alert_type="temperature",
                message="High temperature: 95°F"
            )

        assert result is True
        mock_iot_client.publish.assert_called_once()

    def test_alert_payload_structure(self, sample_aws_config, mock_iot_client):
        """Alert payload should have type, message, timestamp."""
        from src.aws.iot.client import IoTClient

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)
            client.publish_alert(
                coop_id="coop1",
                alert_type="motion",
                message="Motion detected"
            )

        call_kwargs = mock_iot_client.publish.call_args.kwargs
        payload = json.loads(call_kwargs.get('payload', '{}'))

        assert payload["type"] == "motion"
        assert payload["message"] == "Motion detected"
        assert "timestamp" in payload


# =============================================================================
# Test: Publishing Status Updates
# =============================================================================

class TestPublishStatus:
    """Tests for publishing status updates."""

    def test_publish_status_success(self, sample_aws_config, mock_iot_client):
        """Should publish status update."""
        from src.aws.iot.client import IoTClient

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)
            result = client.publish_status(
                coop_id="coop1",
                status="online",
                details={"uptime": 3600}
            )

        assert result is True

    def test_status_payload_contains_details(self, sample_aws_config, mock_iot_client):
        """Status payload should include all details."""
        from src.aws.iot.client import IoTClient

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)
            client.publish_status(
                coop_id="coop1",
                status="online",
                details={"uptime": 3600, "cpu_temp": 45.2}
            )

        call_kwargs = mock_iot_client.publish.call_args.kwargs
        payload = json.loads(call_kwargs.get('payload', '{}'))

        assert payload["status"] == "online"
        assert payload["uptime"] == 3600
        assert payload["cpu_temp"] == 45.2


# =============================================================================
# Test: Error Handling
# =============================================================================

class TestErrorHandling:
    """Tests for IoT error handling."""

    def test_publish_failure_returns_false(self, sample_aws_config, mock_iot_client):
        """Failed publish should return False."""
        from src.aws.iot.client import IoTClient
        from src.models.sensor import SensorReading

        mock_iot_client.publish.side_effect = Exception("Connection failed")

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config)
            reading = SensorReading(
                temperature=72.5,
                humidity=65.0,
                coop_id="coop1"
            )

            result = client.publish_sensor_reading(reading)

        assert result is False

    def test_publish_with_retry(self, sample_aws_config, mock_iot_client):
        """Should retry on transient failures."""
        from src.aws.iot.client import IoTClient
        from src.models.sensor import SensorReading

        # Fail first two times, succeed on third
        mock_iot_client.publish.side_effect = [
            Exception("Timeout"),
            Exception("Timeout"),
            {"ResponseMetadata": {"HTTPStatusCode": 200}}
        ]

        with patch('boto3.client', return_value=mock_iot_client):
            client = IoTClient(sample_aws_config, max_retries=3)
            reading = SensorReading(
                temperature=72.5,
                humidity=65.0,
                coop_id="coop1"
            )

            result = client.publish_sensor_reading(reading)

        assert result is True
        assert mock_iot_client.publish.call_count == 3
