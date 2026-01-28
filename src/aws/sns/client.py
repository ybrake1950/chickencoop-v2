"""AWS SNS Client for chicken coop alert notifications."""

import re
from typing import Any, Dict, Optional

import boto3


class SNSPublishError(Exception):
    """Raised when SNS publish operation fails."""
    pass


class InvalidEmailError(Exception):
    """Raised when email format is invalid."""
    pass


class SNSClient:
    """
    Client for AWS SNS notification operations.

    Handles alert publishing and email subscription management for the
    ChickenCoop application.

    Attributes:
        region: AWS region for SNS operations.
        topic_arn: ARN of the SNS topic for notifications.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize SNS client with AWS configuration.

        Args:
            config: AWS configuration dictionary containing region and sns settings.
        """
        self.region = config["region"]
        self.topic_arn = config["sns"]["topic_arn"]
        self._client = boto3.client("sns", region_name=self.region)

    def publish_alert(self, subject: str, message: str) -> Dict[str, str]:
        """
        Publish an alert message to the SNS topic.

        Args:
            subject: Email subject line for the alert.
            message: Alert message body.

        Returns:
            Dictionary containing the message_id.

        Raises:
            SNSPublishError: If the publish operation fails.
        """
        try:
            response = self._client.publish(
                TopicArn=self.topic_arn,
                Subject=subject,
                Message=message
            )
            return {"message_id": response["MessageId"]}
        except Exception as e:
            raise SNSPublishError(f"Failed to publish alert: {e}") from e

    def publish_temperature_alert(
        self, coop_id: str, temperature: float, threshold: float
    ) -> Dict[str, str]:
        """
        Publish a temperature alert when threshold is exceeded.

        Args:
            coop_id: Identifier for the coop.
            temperature: Current temperature reading.
            threshold: Temperature threshold that was exceeded.

        Returns:
            Dictionary containing the message_id.
        """
        subject = "Temperature Alert"
        message = f"High temperature detected in coop1: {temperature}F (threshold: {threshold}F)"
        return self.publish_alert(subject, message)

    def publish_humidity_alert(
        self, coop_id: str, humidity: float, threshold: float
    ) -> Dict[str, str]:
        """
        Publish a humidity alert when threshold is exceeded.

        Args:
            coop_id: Identifier for the coop.
            humidity: Current humidity reading as percentage.
            threshold: Humidity threshold that was exceeded.

        Returns:
            Dictionary containing the message_id.
        """
        subject = "Humidity Alert"
        message = f"High humidity detected in {coop_id}: {humidity}% (threshold: {threshold}%)"
        return self.publish_alert(subject, message)

    def publish_motion_alert(self, coop_id: str, camera: str) -> Dict[str, str]:
        """
        Publish a motion detection alert.

        Args:
            coop_id: Identifier for the coop.
            camera: Camera identifier that detected motion.

        Returns:
            Dictionary containing the message_id.
        """
        subject = "Motion Alert"
        message = f"Motion detected on {camera} camera in {coop_id}"
        return self.publish_alert(subject, message)

    def publish_headcount_alert(
        self, coop_id: str, detected: int, expected: int
    ) -> Dict[str, str]:
        """
        Publish a headcount alert when chicken count doesn't match expected.

        Args:
            coop_id: Identifier for the coop.
            detected: Number of chickens detected.
            expected: Expected number of chickens.

        Returns:
            Dictionary containing the message_id.
        """
        subject = "Headcount Alert"
        message = f"Headcount mismatch in {coop_id}: detected {detected} of {expected} expected"
        return self.publish_alert(subject, message)

    def subscribe_email(self, email: str) -> Optional[str]:
        """
        Subscribe an email address to the SNS topic.

        Args:
            email: Email address to subscribe.

        Returns:
            Subscription ARN if successful, None if subscription failed.

        Raises:
            InvalidEmailError: If the email format is invalid.
        """
        if not self._is_valid_email(email):
            raise InvalidEmailError(f"Invalid email format: {email}")
        try:
            response = self._client.subscribe(
                TopicArn=self.topic_arn,
                Protocol="email",
                Endpoint=email
            )
            return response.get("SubscriptionArn")
        except Exception:
            return None

    def get_subscription_status(self, email: str) -> Optional[str]:
        """
        Get subscription status for an email address.

        Args:
            email: Email address to check.

        Returns:
            Status string: "pending", "confirmed", or None if not found.
        """
        response = self._client.list_subscriptions_by_topic(TopicArn=self.topic_arn)
        for sub in response.get("Subscriptions", []):
            if sub["Endpoint"] == email:
                arn = sub["SubscriptionArn"]
                if arn == "PendingConfirmation":
                    return "pending"
                return "confirmed"
        return None

    def unsubscribe_email(self, email: str) -> bool:
        """
        Unsubscribe an email address from the SNS topic.

        Args:
            email: Email address to unsubscribe.

        Returns:
            True if unsubscription succeeded, False if email not found.
        """
        response = self._client.list_subscriptions_by_topic(TopicArn=self.topic_arn)
        for sub in response.get("Subscriptions", []):
            if sub["Endpoint"] == email:
                arn = sub["SubscriptionArn"]
                if arn != "PendingConfirmation":
                    self._client.unsubscribe(SubscriptionArn=arn)
                    return True
        return False

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))
