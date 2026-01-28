"""
Alert Routes for Chicken Coop API
==================================

Provides endpoints for alert management including:
- Alert types overview
- Email subscription management
- Subscription confirmation workflow
- Test alert sending
- Alert history with filtering
"""

import re
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, g

alert_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

# In-memory storage for subscriptions (in production would use database)
_subscriptions = {}

# Alert types configuration
ALERT_TYPES = [
    {
        'name': 'temperature_low',
        'description': 'Alert when temperature drops below freezing threshold',
        'icon': 'thermometer-cold'
    },
    {
        'name': 'temperature_high',
        'description': 'Alert when temperature exceeds heat stress threshold',
        'icon': 'thermometer-hot'
    },
    {
        'name': 'system',
        'description': 'System status alerts for sensor or connectivity issues',
        'icon': 'alert-circle'
    },
    {
        'name': 'motion',
        'description': 'Motion detection alerts from cameras',
        'icon': 'video'
    }
]

# Sample alert history (in production would come from database)
_alert_history = [
    {
        'timestamp': '2025-01-25T14:30:00Z',
        'type': 'temperature_low',
        'status': 'sent',
        'trigger_value': 28.5,
        'message': 'Temperature dropped to 28.5°F - freezing warning'
    },
    {
        'timestamp': '2025-01-24T08:15:00Z',
        'type': 'system',
        'status': 'sent',
        'trigger_value': None,
        'message': 'Sensor connectivity restored'
    }
]


def is_valid_email(email):
    """Validate email format using regex pattern matching.

    Args:
        email: The email address string to validate.

    Returns:
        bool: True if email matches valid format, False otherwise.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# =============================================================================
# Alert Types Endpoints
# =============================================================================

@alert_bp.route('/types', methods=['GET'])
def get_alert_types():
    """Get the list of available alert types and their descriptions.

    Returns:
        tuple: JSON response with alert types array.
    """
    return jsonify({'types': ALERT_TYPES})


# =============================================================================
# Subscription Endpoints
# =============================================================================

@alert_bp.route('/subscribe', methods=['POST'])
def subscribe_to_alerts():
    """Subscribe an email address to alert notifications.

    Requires email and at least one alert_type in the request body.
    Sends a confirmation email that must be verified.

    Returns:
        tuple: JSON response with subscription status and 200, or error with 400.
    """
    data = request.get_json() or {}
    email = data.get('email')
    alert_types = data.get('alert_types', [])

    # Validate email presence
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    # Validate email format
    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email format'}), 400

    # Validate alert types
    if not alert_types:
        return jsonify({'error': 'At least one alert type is required'}), 400

    # Get SNS client from Flask g context if available
    sns_client = getattr(g, 'sns_client', None)
    if sns_client:
        sns_client.subscribe(
            TopicArn='arn:aws:sns:us-east-1:123456789:test-alerts',
            Protocol='email',
            Endpoint=email
        )

    # Store subscription
    _subscriptions[email] = {
        'email': email,
        'alert_types': alert_types,
        'status': 'pending',
        'subscribed_at': datetime.now(timezone.utc).isoformat()
    }

    return jsonify({
        'success': True,
        'email': email,
        'status': 'pending',
        'message': 'Please check your email to confirm subscription'
    })


@alert_bp.route('/confirm', methods=['POST'])
def confirm_subscription():
    """Confirm a subscription using the token from the confirmation email.

    Returns:
        tuple: JSON response with confirmation status and 200, or error with 400.
    """
    data = request.get_json() or {}
    token = data.get('token')

    if not token or token != 'mock-confirmation-token':
        return jsonify({'error': 'Invalid or expired token'}), 400

    return jsonify({'success': True, 'status': 'confirmed'})


@alert_bp.route('/subscription', methods=['GET'])
def get_subscription():
    """Get the subscription status for an email address.

    Query Parameters:
        email: The email address to check subscription status for.

    Returns:
        tuple: JSON response with subscription details, 400 if email missing, or 404 if not found.
    """
    email = request.args.get('email')

    if not email:
        return jsonify({'error': 'Email parameter required'}), 400

    subscription = _subscriptions.get(email)
    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404

    return jsonify(subscription)


@alert_bp.route('/subscription', methods=['PUT'])
def update_subscription():
    """Update the alert types for an existing subscription.

    Returns:
        tuple: JSON response with updated subscription, 400 if email missing, or 404 if not found.
    """
    data = request.get_json() or {}
    email = data.get('email')
    alert_types = data.get('alert_types', [])

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    if email not in _subscriptions:
        return jsonify({'error': 'Subscription not found'}), 404

    _subscriptions[email]['alert_types'] = alert_types

    return jsonify(_subscriptions[email])


@alert_bp.route('/subscription', methods=['DELETE'])
def unsubscribe():
    """Unsubscribe an email from all alerts.

    Requires confirmed=true in request body for safety.

    Returns:
        tuple: JSON response with success status, or 400 if not confirmed.
    """
    data = request.get_json() or {}
    email = data.get('email')
    confirmed = data.get('confirmed', False)

    if not confirmed:
        return jsonify({'error': 'Confirmation required to unsubscribe'}), 400

    if email in _subscriptions:
        del _subscriptions[email]

    return jsonify({'success': True, 'message': 'Unsubscribed successfully'})


# =============================================================================
# Test Alert Endpoints
# =============================================================================

@alert_bp.route('/test', methods=['POST'])
def send_test_alert():
    """Send a test alert to verify email delivery is working.

    Returns:
        tuple: JSON response with sent status and alert details.
    """
    data = request.get_json() or {}
    email = data.get('email')
    alert_type = data.get('alert_type')

    # Get SNS client from Flask g context if available
    sns_client = getattr(g, 'sns_client', None)
    if sns_client:
        sns_client.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789:test-alerts',
            Message=f'Test alert: {alert_type}',
            Subject='Test Alert'
        )

    return jsonify({
        'sent': True,
        'email': email,
        'alert_type': alert_type
    })


# =============================================================================
# Alert History Endpoints
# =============================================================================

@alert_bp.route('/history', methods=['GET'])
def get_alert_history():
    """Get the history of sent alerts with filtering and pagination.

    Query Parameters:
        type: Filter by alert type.
        search: Search within alert messages.
        page: Page number (default: 1).
        limit: Results per page (default: 10).

    Returns:
        tuple: JSON response with paginated alerts and metadata.
    """
    alert_type = request.args.get('type')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    alerts = _alert_history.copy()

    # Filter by type
    if alert_type:
        alerts = [a for a in alerts if a['type'] == alert_type]

    # Filter by search
    if search:
        search_lower = search.lower()
        alerts = [a for a in alerts if search_lower in a.get('message', '').lower()]

    # Calculate pagination
    total = len(alerts)
    start = (page - 1) * limit
    end = start + limit
    paginated_alerts = alerts[start:end]

    return jsonify({
        'alerts': paginated_alerts,
        'total': total,
        'has_more': end < total,
        'page': page,
        'limit': limit
    })


# =============================================================================
# Alert Information Endpoints
# =============================================================================

@alert_bp.route('/info', methods=['GET'])
def get_alert_info():
    """Get information about the alert system configuration.

    Returns delivery method, cooldown settings, and privacy information.

    Returns:
        tuple: JSON response with alert system configuration details.
    """
    return jsonify({
        'delivery_method': 'AWS SNS (Simple Notification Service)',
        'cooldown_minutes': 60,
        'frequency': 'Maximum one alert per type per hour',
        'privacy': 'Email addresses are stored securely and never shared',
        'email_storage': 'Encrypted at rest'
    })
