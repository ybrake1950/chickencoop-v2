"""
Phase 12: Webhook Notifications
================================

Provides webhook-based alert delivery for Slack, Discord, and custom endpoints.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@dataclass
class WebhookConfig:
    """Configuration for a webhook endpoint."""

    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    method: str = "POST"
    payload_template: Optional[str] = None


@dataclass
class WebhookPayload:
    """Structured alert payload for webhook delivery."""

    alert_type: str
    value: float
    threshold: Optional[float]
    coop_id: Optional[str]
    timestamp: Optional[str]

    @classmethod
    def from_alert(cls, alert: Dict[str, Any]) -> "WebhookPayload":
        return cls(
            alert_type=alert.get("type", ""),
            value=alert.get("value", 0),
            threshold=alert.get("threshold"),
            coop_id=alert.get("coop_id"),
            timestamp=alert.get("timestamp"),
        )


@dataclass
class WebhookResult:
    """Result of a webhook delivery attempt."""

    success: bool
    status_code: Optional[int] = None
    error: Optional[str] = None


class WebhookNotifier:
    """Generic webhook notifier with retry support."""

    max_retries: int = 3

    def __init__(self, config: WebhookConfig) -> None:
        self.config = config

    def format_message(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Format an alert into a webhook-compatible payload."""
        return {"alert": alert}

    def send(self, alert: Dict[str, Any], max_retries: int = 1) -> WebhookResult:
        """Send an alert via webhook with retry and exponential backoff on failure."""
        payload = self.format_message(alert)
        delays = self.get_retry_delays(max_retries)

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.config.url,
                    json=payload,
                    headers=self.config.headers,
                    timeout=30,
                )
                if response.ok:
                    return WebhookResult(success=True, status_code=response.status_code)
                if 400 <= response.status_code < 500:
                    logger.warning(
                        "Webhook failed with client error %d", response.status_code
                    )
                    return WebhookResult(
                        success=False, status_code=response.status_code
                    )
                # 5xx — retry
                logger.warning(
                    "Webhook failed with server error %d, retrying",
                    response.status_code,
                )
                if attempt < max_retries - 1:
                    time.sleep(delays[attempt])
            except requests.exceptions.Timeout:
                logger.warning("Webhook timed out, retrying")
                if attempt < max_retries - 1:
                    time.sleep(delays[attempt])
            except requests.exceptions.RequestException as exc:
                logger.warning("Webhook request failed: %s", exc)
                return WebhookResult(success=False, error=str(exc))

        logger.warning("Webhook delivery failed after %d attempts", max_retries)
        return WebhookResult(success=False)

    def get_retry_delays(self, max_retries: int = 3) -> List[float]:
        """Return exponential backoff delays in seconds for each retry attempt."""
        return [0.1 * (2**i) for i in range(max_retries)]


class SlackNotifier:
    """Slack-specific webhook notifier."""

    SEVERITY_COLORS = {
        "info": "#36a64f",
        "warning": "#ff9900",
        "critical": "#ff0000",
    }

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def format_message(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Format an alert into a Slack attachment payload with severity-based color."""
        severity = alert.get("severity", "info")
        color = self.SEVERITY_COLORS.get(severity, "#439FE0")
        fields = []
        if "type" in alert:
            fields.append({"title": "Type", "value": alert["type"], "short": True})
        if "value" in alert:
            fields.append(
                {"title": "Value", "value": str(alert["value"]), "short": True}
            )
        if "timestamp" in alert:
            fields.append(
                {"title": "Timestamp", "value": alert["timestamp"], "short": False}
            )

        return {
            "attachments": [
                {
                    "color": color,
                    "title": f"Coop Alert: {alert.get('type', 'unknown')}",
                    "text": alert.get("message", ""),
                    "fields": fields,
                    "ts": alert.get("timestamp", ""),
                }
            ]
        }

    def send(self, alert: Dict[str, Any], _max_retries: int = 1) -> WebhookResult:
        """Send an alert to Slack via incoming webhook."""
        payload = self.format_message(alert)
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=30)
            return WebhookResult(success=response.ok, status_code=response.status_code)
        except requests.exceptions.RequestException as exc:
            logger.warning("Slack webhook failed: %s", exc)
            return WebhookResult(success=False, error=str(exc))


class DiscordNotifier:
    """Discord-specific webhook notifier."""

    SEVERITY_COLORS = {
        "info": 0x36A64F,
        "warning": 0xFF9900,
        "critical": 0xFF0000,
    }

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def format_message(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Format an alert into a Discord embed payload with severity-based color."""
        severity = alert.get("severity", "info")
        color = self.SEVERITY_COLORS.get(severity, 0x439FE0)
        embed_fields = []
        if "type" in alert:
            embed_fields.append(
                {"name": "Type", "value": alert["type"], "inline": True}
            )
        if "value" in alert:
            embed_fields.append(
                {"name": "Value", "value": str(alert["value"]), "inline": True}
            )
        if "timestamp" in alert:
            embed_fields.append(
                {"name": "Timestamp", "value": alert["timestamp"], "inline": False}
            )

        return {
            "embeds": [
                {
                    "title": f"Coop Alert: {alert.get('type', 'unknown')}",
                    "description": alert.get("message", ""),
                    "color": color,
                    "fields": embed_fields,
                }
            ]
        }

    def send(self, alert: Dict[str, Any], _max_retries: int = 1) -> WebhookResult:
        """Send an alert to Discord via incoming webhook."""
        payload = self.format_message(alert)
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=30)
            return WebhookResult(success=response.ok, status_code=response.status_code)
        except requests.exceptions.RequestException as exc:
            logger.warning("Discord webhook failed: %s", exc)
            return WebhookResult(success=False, error=str(exc))
