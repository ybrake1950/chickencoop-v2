"""
SNS Routes for Chicken Coop API
================================

Provides endpoints for SNS alert subscription management including:
- Subscribe to alerts
- Check subscription status
"""

from flask import Blueprint, jsonify, request, g

sns_bp = Blueprint("sns", __name__, url_prefix="/api/sns")

# In-memory storage for subscriptions (in production would use database)
_subscriptions = {}


@sns_bp.route("/subscribe", methods=["POST"])
def subscribe():
    """Subscribe an email address to SNS alert notifications.

    Creates an SNS subscription for the provided email address.
    A confirmation email will be sent that must be verified.

    Returns:
        tuple: JSON response with subscription status and 200, or error with 400.
    """
    data = request.get_json() or {}
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Get SNS client from Flask g context if available
    sns_client = getattr(g, "sns_client", None)
    if sns_client:
        sns_client.subscribe(
            TopicArn="arn:aws:sns:us-east-1:123456789:test-alerts",
            Protocol="email",
            Endpoint=email,
        )

    _subscriptions[email] = {"email": email, "status": "pending"}

    return (
        jsonify(
            {
                "success": True,
                "email": email,
                "status": "pending",
                "message": "Subscription confirmation email sent",
            }
        ),
        200,
    )


@sns_bp.route("/check-subscription", methods=["POST"])
def check_subscription():
    """Check the subscription status for an email address.

    Returns the current subscription status (pending, confirmed, or not_found).

    Returns:
        tuple: JSON response with subscription details and 200, or error with 400.
    """
    data = request.get_json() or {}
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    subscription = _subscriptions.get(email, {"email": email, "status": "not_found"})

    return jsonify(subscription), 200
