"""
TDD Tests: AWS SNS Client

These tests define the expected behavior for SNS notification operations.
Implement src/aws/sns/client.py to make these tests pass.

Run: pytest tdd/phase4_aws/sns/test_sns_client.py -v

FUNCTIONALITY BEING TESTED:
- SNS client initialization with configuration
- Publishing alert messages to SNS topics
- Email subscription management
- Subscription confirmation status checking
- Message formatting for different alert types
- Error handling for publish failures

WHY THIS MATTERS:
SNS sends email/SMS alerts when temperatures exceed thresholds or chickens
are missing from headcount. Users subscribe to receive these notifications
to protect their flock.

HOW TESTS ARE EXECUTED:
1. Tests use mock_sns_client fixture (mocked boto3 SNS client)
2. SNSClient class wraps the boto3 client
3. Publish and subscribe operations are tested
4. Message structure and ARN formats are validated
"""

import pytest
from unittest.mock import MagicMock, patch


# =============================================================================
# Test: SNS Client Initialization
# =============================================================================

class TestSNSClientInit:
    """Tests for SNS client initialization."""

    def test_client_initializes_with_config(self, sample_aws_config, mock_sns_client):
        """SNSClient should initialize with AWS configuration."""
        from src.aws.sns.client import SNSClient

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)

        assert client is not None

    def test_client_uses_configured_topic_arn(self, sample_aws_config, mock_sns_client):
        """Client should use topic ARN from config."""
        from src.aws.sns.client import SNSClient

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)

        assert client.topic_arn == sample_aws_config["sns"]["topic_arn"]

    def test_client_uses_configured_region(self, sample_aws_config, mock_sns_client):
        """Client should use AWS region from config."""
        from src.aws.sns.client import SNSClient

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)

        assert client.region == sample_aws_config["region"]


# =============================================================================
# Test: Publishing Alerts
# =============================================================================

class TestPublishAlert:
    """Tests for publishing alert messages."""

    def test_publish_returns_message_id(self, sample_aws_config, mock_sns_client):
        """Successful publish should return message ID."""
        from src.aws.sns.client import SNSClient

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            result = client.publish_alert(
                subject="Temperature Alert",
                message="High temperature detected: 95°F"
            )

        assert result is not None
        assert "message_id" in result or isinstance(result, str)

    def test_publish_calls_sns_publish(self, sample_aws_config, mock_sns_client):
        """Should call SNS publish method."""
        from src.aws.sns.client import SNSClient

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            client.publish_alert(
                subject="Test Alert",
                message="Test message"
            )

        mock_sns_client.publish.assert_called_once()

    def test_publish_uses_correct_topic_arn(self, sample_aws_config, mock_sns_client):
        """Should publish to configured topic ARN."""
        from src.aws.sns.client import SNSClient

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            client.publish_alert(
                subject="Test Alert",
                message="Test message"
            )

        call_kwargs = mock_sns_client.publish.call_args.kwargs
        assert call_kwargs["TopicArn"] == sample_aws_config["sns"]["topic_arn"]

    def test_publish_includes_subject(self, sample_aws_config, mock_sns_client):
        """Published message should include subject."""
        from src.aws.sns.client import SNSClient

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            client.publish_alert(
                subject="Temperature Alert",
                message="High temperature"
            )

        call_kwargs = mock_sns_client.publish.call_args.kwargs
        assert call_kwargs["Subject"] == "Temperature Alert"


# =============================================================================
# Test: Alert Types
# =============================================================================

class TestAlertTypes:
    """Tests for different alert types."""

    def test_publish_temperature_alert(self, sample_aws_config, mock_sns_client):
        """Should publish temperature alert with formatted message."""
        from src.aws.sns.client import SNSClient

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            client.publish_temperature_alert(
                coop_id="coop1",
                temperature=95.0,
                threshold=90.0
            )

        call_kwargs = mock_sns_client.publish.call_args.kwargs
        assert "temperature" in call_kwargs["Subject"].lower()
        assert "95" in call_kwargs["Message"]
        assert "coop1" in call_kwargs["Message"].lower()

    def test_publish_humidity_alert(self, sample_aws_config, mock_sns_client):
        """Should publish humidity alert with formatted message."""
        from src.aws.sns.client import SNSClient

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            client.publish_humidity_alert(
                coop_id="coop1",
                humidity=85.0,
                threshold=80.0
            )

        call_kwargs = mock_sns_client.publish.call_args.kwargs
        assert "humidity" in call_kwargs["Subject"].lower()
        assert "85" in call_kwargs["Message"]

    def test_publish_motion_alert(self, sample_aws_config, mock_sns_client):
        """Should publish motion detection alert."""
        from src.aws.sns.client import SNSClient

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            client.publish_motion_alert(
                coop_id="coop1",
                camera="outdoor"
            )

        call_kwargs = mock_sns_client.publish.call_args.kwargs
        assert "motion" in call_kwargs["Subject"].lower()
        assert "outdoor" in call_kwargs["Message"].lower()

    def test_publish_headcount_alert(self, sample_aws_config, mock_sns_client):
        """Should publish missing chicken alert."""
        from src.aws.sns.client import SNSClient

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            client.publish_headcount_alert(
                coop_id="coop1",
                detected=5,
                expected=6
            )

        call_kwargs = mock_sns_client.publish.call_args.kwargs
        assert "headcount" in call_kwargs["Subject"].lower() or "chicken" in call_kwargs["Subject"].lower()
        assert "5" in call_kwargs["Message"]
        assert "6" in call_kwargs["Message"]


# =============================================================================
# Test: Email Subscription
# =============================================================================

class TestEmailSubscription:
    """Tests for email subscription management."""

    def test_subscribe_email_returns_arn(self, sample_aws_config, mock_sns_client):
        """Subscribing email should return subscription ARN."""
        from src.aws.sns.client import SNSClient

        mock_sns_client.subscribe.return_value = {
            "SubscriptionArn": "pending confirmation"
        }

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            result = client.subscribe_email("user@example.com")

        assert result is not None

    def test_subscribe_calls_sns_subscribe(self, sample_aws_config, mock_sns_client):
        """Should call SNS subscribe method."""
        from src.aws.sns.client import SNSClient

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            client.subscribe_email("user@example.com")

        mock_sns_client.subscribe.assert_called_once()

    def test_subscribe_uses_email_protocol(self, sample_aws_config, mock_sns_client):
        """Should use 'email' protocol for email subscriptions."""
        from src.aws.sns.client import SNSClient

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            client.subscribe_email("user@example.com")

        call_kwargs = mock_sns_client.subscribe.call_args.kwargs
        assert call_kwargs["Protocol"] == "email"
        assert call_kwargs["Endpoint"] == "user@example.com"

    def test_check_subscription_status_pending(self, sample_aws_config, mock_sns_client):
        """Should detect pending confirmation status."""
        from src.aws.sns.client import SNSClient

        mock_sns_client.list_subscriptions_by_topic.return_value = {
            "Subscriptions": [
                {
                    "Endpoint": "user@example.com",
                    "SubscriptionArn": "PendingConfirmation"
                }
            ]
        }

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            status = client.get_subscription_status("user@example.com")

        assert status == "pending"

    def test_check_subscription_status_confirmed(self, sample_aws_config, mock_sns_client):
        """Should detect confirmed subscription status."""
        from src.aws.sns.client import SNSClient

        mock_sns_client.list_subscriptions_by_topic.return_value = {
            "Subscriptions": [
                {
                    "Endpoint": "user@example.com",
                    "SubscriptionArn": "arn:aws:sns:us-east-1:123:topic:abc123"
                }
            ]
        }

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            status = client.get_subscription_status("user@example.com")

        assert status == "confirmed"

    def test_check_subscription_status_not_found(self, sample_aws_config, mock_sns_client):
        """Should return None for non-existent subscription."""
        from src.aws.sns.client import SNSClient

        mock_sns_client.list_subscriptions_by_topic.return_value = {
            "Subscriptions": []
        }

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            status = client.get_subscription_status("user@example.com")

        assert status is None

    def test_unsubscribe_email(self, sample_aws_config, mock_sns_client):
        """Should unsubscribe email from topic."""
        from src.aws.sns.client import SNSClient

        mock_sns_client.list_subscriptions_by_topic.return_value = {
            "Subscriptions": [
                {
                    "Endpoint": "user@example.com",
                    "SubscriptionArn": "arn:aws:sns:us-east-1:123:topic:abc123"
                }
            ]
        }

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)
            result = client.unsubscribe_email("user@example.com")

        assert result is True
        mock_sns_client.unsubscribe.assert_called_once()


# =============================================================================
# Test: Error Handling
# =============================================================================

class TestErrorHandling:
    """Tests for SNS error handling."""

    def test_publish_failure_raises_exception(self, sample_aws_config, mock_sns_client):
        """Failed publish should raise or return error."""
        from src.aws.sns.client import SNSClient, SNSPublishError

        mock_sns_client.publish.side_effect = Exception("Publish failed")

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)

            with pytest.raises((SNSPublishError, Exception)):
                client.publish_alert(
                    subject="Test",
                    message="Test message"
                )

    def test_invalid_email_format_raises(self, sample_aws_config, mock_sns_client):
        """Should reject invalid email format."""
        from src.aws.sns.client import SNSClient, InvalidEmailError

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)

            with pytest.raises((InvalidEmailError, ValueError)):
                client.subscribe_email("not-an-email")

    def test_subscribe_failure_returns_none(self, sample_aws_config, mock_sns_client):
        """Failed subscription should return None or raise."""
        from src.aws.sns.client import SNSClient

        mock_sns_client.subscribe.side_effect = Exception("Subscribe failed")

        with patch('boto3.client', return_value=mock_sns_client):
            client = SNSClient(sample_aws_config)

            try:
                result = client.subscribe_email("user@example.com")
                assert result is None
            except Exception:
                pass  # Exception is also acceptable
