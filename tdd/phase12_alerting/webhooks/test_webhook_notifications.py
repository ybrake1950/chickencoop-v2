"""
Phase 12: Webhook Notifications Tests
=====================================

FUNCTIONALITY BEING TESTED:
---------------------------
- Slack webhook integration
- Discord webhook integration
- Custom webhook delivery
- Webhook payload formatting
- Retry logic for failed deliveries

WHY THIS MATTERS:
-----------------
Email isn't always the best notification channel. Webhooks enable
integration with team chat tools, custom dashboards, and third-party
systems for real-time alerts.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase12_alerting/webhooks/test_webhook_notifications.py -v
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.alerting.webhooks import (
    WebhookNotifier,
    SlackNotifier,
    DiscordNotifier,
    WebhookConfig,
    WebhookPayload,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def slack_notifier():
    """Provide a Slack notifier."""
    return SlackNotifier(webhook_url="https://hooks.slack.com/services/test/webhook")

@pytest.fixture
def discord_notifier():
    """Provide a Discord notifier."""
    return DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test/webhook")

@pytest.fixture
def custom_notifier():
    """Provide a custom webhook notifier."""
    config = WebhookConfig(
        url="https://example.com/webhook",
        headers={"Authorization": "Bearer test-token", "X-Custom": "value"},
        method="POST"
    )
    return WebhookNotifier(config=config)

@pytest.fixture
def sample_alert():
    """Provide a sample alert payload."""
    return {
        "type": "temperature_high",
        "severity": "warning",
        "value": 105.2,
        "threshold": 100.0,
        "coop_id": "coop1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Temperature exceeded threshold"
    }


# =============================================================================
# TestSlackIntegration
# =============================================================================

class TestSlackIntegration:
    """Test Slack webhook integration."""

    def test_slack_webhook_configured(self, slack_notifier):
        """Slack webhook URL can be configured."""
        assert slack_notifier.webhook_url is not None
        assert "hooks.slack.com" in slack_notifier.webhook_url

    def test_slack_message_format(self, slack_notifier, sample_alert):
        """Slack messages properly formatted."""
        payload = slack_notifier.format_message(sample_alert)
        assert "text" in payload or "blocks" in payload or "attachments" in payload

    def test_slack_includes_alert_details(self, slack_notifier, sample_alert):
        """Slack message includes alert details."""
        payload = slack_notifier.format_message(sample_alert)
        payload_str = str(payload)
        assert "temperature" in payload_str.lower() or "105" in payload_str

    def test_slack_includes_timestamp(self, slack_notifier, sample_alert):
        """Slack message includes timestamp."""
        payload = slack_notifier.format_message(sample_alert)
        payload_str = str(payload)
        assert "timestamp" in payload_str.lower() or "ts" in payload

    def test_slack_color_by_severity(self, slack_notifier):
        """Slack attachment color reflects severity."""
        warning_payload = slack_notifier.format_message({
            "type": "temperature_high", "severity": "warning", "value": 95
        })
        critical_payload = slack_notifier.format_message({
            "type": "temperature_high", "severity": "critical", "value": 120
        })
        # Colors should differ for different severities
        assert warning_payload != critical_payload

    @patch("src.alerting.webhooks.requests.post")
    def test_slack_delivery_success(self, mock_post, slack_notifier, sample_alert):
        """Slack webhook delivery succeeds."""
        mock_post.return_value = MagicMock(status_code=200, ok=True)
        result = slack_notifier.send(sample_alert)
        assert result.success is True
        mock_post.assert_called_once()


# =============================================================================
# TestDiscordIntegration
# =============================================================================

class TestDiscordIntegration:
    """Test Discord webhook integration."""

    def test_discord_webhook_configured(self, discord_notifier):
        """Discord webhook URL can be configured."""
        assert discord_notifier.webhook_url is not None
        assert "discord.com" in discord_notifier.webhook_url

    def test_discord_embed_format(self, discord_notifier, sample_alert):
        """Discord embeds properly formatted."""
        payload = discord_notifier.format_message(sample_alert)
        assert "embeds" in payload or "content" in payload

    def test_discord_includes_alert_details(self, discord_notifier, sample_alert):
        """Discord message includes alert details."""
        payload = discord_notifier.format_message(sample_alert)
        payload_str = str(payload)
        assert "temperature" in payload_str.lower() or "105" in payload_str

    @patch("src.alerting.webhooks.requests.post")
    def test_discord_delivery_success(self, mock_post, discord_notifier, sample_alert):
        """Discord webhook delivery succeeds."""
        mock_post.return_value = MagicMock(status_code=204, ok=True)
        result = discord_notifier.send(sample_alert)
        assert result.success is True


# =============================================================================
# TestCustomWebhooks
# =============================================================================

class TestCustomWebhooks:
    """Test custom webhook support."""

    def test_custom_webhook_url(self, custom_notifier):
        """Custom webhook URL supported."""
        assert custom_notifier.config.url == "https://example.com/webhook"

    def test_custom_payload_template(self):
        """Custom payload template supported."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            payload_template='{"alert": "{{type}}", "val": {{value}}}'
        )
        notifier = WebhookNotifier(config=config)
        assert notifier.config.payload_template is not None

    def test_custom_headers(self, custom_notifier):
        """Custom headers can be added."""
        assert "X-Custom" in custom_notifier.config.headers
        assert custom_notifier.config.headers["X-Custom"] == "value"

    def test_custom_auth_header(self, custom_notifier):
        """Authorization header supported."""
        assert "Authorization" in custom_notifier.config.headers
        assert "Bearer" in custom_notifier.config.headers["Authorization"]

    @patch("src.alerting.webhooks.requests.post")
    def test_json_payload_delivery(self, mock_post, custom_notifier, sample_alert):
        """JSON payload delivered correctly."""
        mock_post.return_value = MagicMock(status_code=200, ok=True)
        result = custom_notifier.send(sample_alert)
        assert result.success is True
        call_kwargs = mock_post.call_args
        assert "json" in call_kwargs.kwargs or "data" in call_kwargs.kwargs


# =============================================================================
# TestWebhookPayload
# =============================================================================

class TestWebhookPayload:
    """Test webhook payload formatting."""

    def test_payload_includes_alert_type(self, sample_alert):
        """Payload includes alert type."""
        payload = WebhookPayload.from_alert(sample_alert)
        assert payload.alert_type == "temperature_high"

    def test_payload_includes_value(self, sample_alert):
        """Payload includes triggering value."""
        payload = WebhookPayload.from_alert(sample_alert)
        assert payload.value == 105.2

    def test_payload_includes_threshold(self, sample_alert):
        """Payload includes threshold that was violated."""
        payload = WebhookPayload.from_alert(sample_alert)
        assert payload.threshold == 100.0

    def test_payload_includes_coop_id(self, sample_alert):
        """Payload includes coop identifier."""
        payload = WebhookPayload.from_alert(sample_alert)
        assert payload.coop_id == "coop1"

    def test_payload_includes_timestamp(self, sample_alert):
        """Payload includes ISO timestamp."""
        payload = WebhookPayload.from_alert(sample_alert)
        assert payload.timestamp is not None
        assert "T" in payload.timestamp  # ISO format


# =============================================================================
# TestWebhookRetry
# =============================================================================

class TestWebhookRetry:
    """Test webhook retry logic."""

    @patch("src.alerting.webhooks.requests.post")
    def test_retry_on_timeout(self, mock_post, custom_notifier, sample_alert):
        """Webhook retried on timeout."""
        from requests.exceptions import Timeout
        mock_post.side_effect = [Timeout("Connection timed out"), MagicMock(status_code=200, ok=True)]
        result = custom_notifier.send(sample_alert, max_retries=2)
        assert result.success is True
        assert mock_post.call_count == 2

    @patch("src.alerting.webhooks.requests.post")
    def test_retry_on_5xx(self, mock_post, custom_notifier, sample_alert):
        """Webhook retried on server error."""
        mock_post.side_effect = [
            MagicMock(status_code=503, ok=False),
            MagicMock(status_code=200, ok=True)
        ]
        result = custom_notifier.send(sample_alert, max_retries=2)
        assert result.success is True

    @patch("src.alerting.webhooks.requests.post")
    def test_no_retry_on_4xx(self, mock_post, custom_notifier, sample_alert):
        """Webhook not retried on client error."""
        mock_post.return_value = MagicMock(status_code=400, ok=False)
        result = custom_notifier.send(sample_alert, max_retries=3)
        assert result.success is False
        assert mock_post.call_count == 1  # No retries for 4xx

    def test_exponential_backoff(self, custom_notifier):
        """Retries use exponential backoff."""
        delays = custom_notifier.get_retry_delays(max_retries=4)
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]

    def test_max_retries_limited(self, custom_notifier):
        """Maximum retry attempts limited."""
        assert custom_notifier.max_retries <= 5

    @patch("src.alerting.webhooks.requests.post")
    def test_failed_webhook_logged(self, mock_post, custom_notifier, sample_alert, caplog):
        """Failed webhook delivery logged."""
        import logging
        caplog.set_level(logging.WARNING)
        mock_post.return_value = MagicMock(status_code=500, ok=False)
        custom_notifier.send(sample_alert, max_retries=1)
        assert "webhook" in caplog.text.lower() or "failed" in caplog.text.lower() or len(caplog.records) > 0
