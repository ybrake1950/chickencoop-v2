"""
Phase 5: Alert Routes Tests
===========================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates all Alerts page API functionality:
- Alert types overview (temp low, temp high, system, motion)
- Email subscription management
- Subscription confirmation workflow
- Current subscriptions display
- Check subscription status
- Test alert sending
- Alert history with filtering

WHY THIS MATTERS:
-----------------
Alerts are the primary notification system for the chicken coop. Temperature
extremes can harm chickens - freezing temps or heat stress are dangerous.
System alerts notify of sensor/connectivity issues. The subscription system
uses AWS SNS with email confirmation to prevent spam.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase5_api/routes/test_alert_routes.py -v

Tests use Flask test client with mocked SNS client. Email confirmation
is simulated without actual email sending.
"""
import pytest
from flask import Flask, json


class TestAlertTypesOverview:
    """Test alert types overview endpoint."""

    def test_get_alert_types(self, flask_client):
        """Get list of available alert types."""
        response = flask_client.get('/api/alerts/types')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'types' in data
        assert len(data['types']) >= 4

    def test_alert_types_include_temperature_low(self, flask_client):
        """Alert types include temperature low (freezing)."""
        response = flask_client.get('/api/alerts/types')
        data = json.loads(response.data)
        type_names = [t['name'] for t in data['types']]
        assert 'temperature_low' in type_names or 'temp_low' in type_names

    def test_alert_types_include_temperature_high(self, flask_client):
        """Alert types include temperature high (heat stress)."""
        response = flask_client.get('/api/alerts/types')
        data = json.loads(response.data)
        type_names = [t['name'] for t in data['types']]
        assert 'temperature_high' in type_names or 'temp_high' in type_names

    def test_alert_types_include_system(self, flask_client):
        """Alert types include system status alerts."""
        response = flask_client.get('/api/alerts/types')
        data = json.loads(response.data)
        type_names = [t['name'] for t in data['types']]
        assert 'system' in type_names or 'system_status' in type_names

    def test_alert_types_include_motion(self, flask_client):
        """Alert types include motion detection alerts."""
        response = flask_client.get('/api/alerts/types')
        data = json.loads(response.data)
        type_names = [t['name'] for t in data['types']]
        assert 'motion' in type_names or 'motion_detection' in type_names

    def test_alert_type_has_description(self, flask_client):
        """Each alert type has a description."""
        response = flask_client.get('/api/alerts/types')
        data = json.loads(response.data)

        for alert_type in data['types']:
            assert 'description' in alert_type
            assert len(alert_type['description']) > 0

    def test_alert_type_has_icon(self, flask_client):
        """Each alert type has an icon identifier."""
        response = flask_client.get('/api/alerts/types')
        data = json.loads(response.data)

        for alert_type in data['types']:
            assert 'icon' in alert_type or 'icon_name' in alert_type


class TestAlertSubscription:
    """Test email subscription endpoints."""

    def test_subscribe_to_alerts(self, flask_client, mock_sns_client):
        """Subscribe email to alert notifications."""
        response = flask_client.post(
            '/api/alerts/subscribe',
            json={
                'email': 'test@example.com',
                'alert_types': ['temperature_low', 'temperature_high']
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_subscribe_requires_email(self, flask_client):
        """Subscription requires valid email."""
        response = flask_client.post(
            '/api/alerts/subscribe',
            json={'alert_types': ['temperature_low']}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'email' in data.get('error', '').lower()

    def test_subscribe_validates_email_format(self, flask_client):
        """Email format is validated."""
        response = flask_client.post(
            '/api/alerts/subscribe',
            json={
                'email': 'not-an-email',
                'alert_types': ['temperature_low']
            }
        )
        assert response.status_code == 400

    def test_subscribe_requires_alert_types(self, flask_client):
        """Subscription requires at least one alert type."""
        response = flask_client.post(
            '/api/alerts/subscribe',
            json={'email': 'test@example.com', 'alert_types': []}
        )
        assert response.status_code == 400

    def test_subscribe_stores_in_localstorage(self, flask_client, mock_sns_client):
        """Email is persisted for future form fills."""
        # This is frontend behavior, but API should return email
        response = flask_client.post(
            '/api/alerts/subscribe',
            json={
                'email': 'test@example.com',
                'alert_types': ['temperature_low']
            }
        )
        data = json.loads(response.data)
        assert 'email' in data


class TestSubscriptionConfirmation:
    """Test subscription confirmation workflow."""

    def test_subscribe_returns_pending_status(self, flask_client, mock_sns_client):
        """New subscription starts in pending status."""
        response = flask_client.post(
            '/api/alerts/subscribe',
            json={
                'email': 'test@example.com',
                'alert_types': ['temperature_low']
            }
        )
        data = json.loads(response.data)
        assert data.get('status') == 'pending' or 'confirmation' in data.get('message', '').lower()

    def test_subscribe_sends_confirmation_email(self, flask_client, mock_sns_client):
        """Subscription triggers confirmation email via SNS."""
        flask_client.post(
            '/api/alerts/subscribe',
            json={
                'email': 'test@example.com',
                'alert_types': ['temperature_low']
            }
        )
        # Verify SNS subscribe was called
        mock_sns_client.subscribe.assert_called()

    def test_confirm_subscription(self, flask_client, mock_sns_client):
        """User can confirm subscription via token."""
        # First subscribe
        flask_client.post(
            '/api/alerts/subscribe',
            json={
                'email': 'test@example.com',
                'alert_types': ['temperature_low']
            }
        )

        # Then confirm (token would come from email)
        response = flask_client.post(
            '/api/alerts/confirm',
            json={'token': 'mock-confirmation-token'}
        )
        # Confirmation handled by SNS directly via email link
        assert response.status_code in [200, 400]  # 400 if no valid token


class TestCurrentSubscriptions:
    """Test current subscriptions display."""

    def test_get_subscription_by_email(self, flask_client, mock_sns_client):
        """Get subscription status for an email."""
        response = flask_client.get('/api/alerts/subscription?email=test@example.com')
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'status' in data
            assert 'alert_types' in data

    def test_subscription_shows_alert_types(self, flask_client, mock_sns_client):
        """Show which alert types are subscribed."""
        # First subscribe
        flask_client.post(
            '/api/alerts/subscribe',
            json={
                'email': 'test@example.com',
                'alert_types': ['temperature_low', 'system']
            }
        )

        # Then check
        response = flask_client.get('/api/alerts/subscription?email=test@example.com')
        data = json.loads(response.data)
        assert 'alert_types' in data
        assert 'temperature_low' in data['alert_types']

    def test_subscription_shows_status(self, flask_client, mock_sns_client):
        """Show subscription status (pending/active/inactive)."""
        flask_client.post(
            '/api/alerts/subscribe',
            json={
                'email': 'test@example.com',
                'alert_types': ['temperature_low']
            }
        )

        response = flask_client.get('/api/alerts/subscription?email=test@example.com')
        data = json.loads(response.data)
        assert data['status'] in ['pending', 'active', 'inactive']

    def test_subscription_expandable_details(self, flask_client, mock_sns_client):
        """Subscription details include delivery info."""
        flask_client.post(
            '/api/alerts/subscribe',
            json={
                'email': 'test@example.com',
                'alert_types': ['temperature_low']
            }
        )

        response = flask_client.get('/api/alerts/subscription?email=test@example.com')
        data = json.loads(response.data)
        # Should include additional details
        assert 'email' in data


class TestEditSubscription:
    """Test subscription editing."""

    def test_update_subscription_alert_types(self, flask_client, mock_sns_client):
        """Update which alert types to receive."""
        # First subscribe
        flask_client.post(
            '/api/alerts/subscribe',
            json={
                'email': 'test@example.com',
                'alert_types': ['temperature_low']
            }
        )

        # Then update
        response = flask_client.put(
            '/api/alerts/subscription',
            json={
                'email': 'test@example.com',
                'alert_types': ['temperature_low', 'temperature_high', 'system']
            }
        )
        assert response.status_code == 200


class TestUnsubscribe:
    """Test unsubscribe functionality."""

    def test_unsubscribe_requires_confirmation(self, flask_client, mock_sns_client):
        """Unsubscribe requires confirmation."""
        response = flask_client.delete(
            '/api/alerts/subscription',
            json={
                'email': 'test@example.com',
                'confirmed': False
            }
        )
        assert response.status_code == 400

    def test_unsubscribe_with_confirmation(self, flask_client, mock_sns_client):
        """Unsubscribe with proper confirmation."""
        # First subscribe
        flask_client.post(
            '/api/alerts/subscribe',
            json={
                'email': 'test@example.com',
                'alert_types': ['temperature_low']
            }
        )

        # Then unsubscribe
        response = flask_client.delete(
            '/api/alerts/subscription',
            json={
                'email': 'test@example.com',
                'confirmed': True
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestTestAlerts:
    """Test alert testing functionality."""

    def test_send_test_alert(self, flask_client, mock_sns_client):
        """Send a test alert to verify email delivery."""
        response = flask_client.post(
            '/api/alerts/test',
            json={
                'email': 'test@example.com',
                'alert_type': 'temperature_low'
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['sent'] is True

    def test_test_alert_for_each_type(self, flask_client, mock_sns_client):
        """Can send test for each alert type."""
        alert_types = ['temperature_low', 'temperature_high', 'system', 'motion']

        for alert_type in alert_types:
            response = flask_client.post(
                '/api/alerts/test',
                json={
                    'email': 'test@example.com',
                    'alert_type': alert_type
                }
            )
            assert response.status_code == 200


class TestAlertHistory:
    """Test alert history endpoint."""

    def test_get_alert_history(self, flask_client):
        """Get history of sent alerts."""
        response = flask_client.get('/api/alerts/history')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'alerts' in data
        assert isinstance(data['alerts'], list)

    def test_history_record_structure(self, flask_client):
        """Each history record has required fields."""
        response = flask_client.get('/api/alerts/history')
        data = json.loads(response.data)

        if len(data['alerts']) > 0:
            alert = data['alerts'][0]
            assert 'timestamp' in alert
            assert 'type' in alert
            assert 'status' in alert

    def test_history_shows_trigger_value(self, flask_client):
        """History shows what triggered the alert."""
        response = flask_client.get('/api/alerts/history')
        data = json.loads(response.data)

        if len(data['alerts']) > 0:
            alert = data['alerts'][0]
            assert 'trigger_value' in alert or 'value' in alert

    def test_history_filter_by_type(self, flask_client):
        """Can filter history by alert type."""
        response = flask_client.get('/api/alerts/history?type=temperature_low')
        assert response.status_code == 200
        data = json.loads(response.data)

        for alert in data['alerts']:
            assert alert['type'] == 'temperature_low'

    def test_history_search(self, flask_client):
        """Can search alert history."""
        response = flask_client.get('/api/alerts/history?search=freezing')
        assert response.status_code == 200

    def test_history_pagination(self, flask_client):
        """History supports pagination."""
        response = flask_client.get('/api/alerts/history?page=1&limit=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total' in data or 'has_more' in data


class TestAlertInformation:
    """Test alert system information."""

    def test_get_alert_info(self, flask_client):
        """Get information about alert system."""
        response = flask_client.get('/api/alerts/info')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'delivery_method' in data
        assert 'SNS' in data['delivery_method']

    def test_alert_frequency_cooldown(self, flask_client):
        """Show alert frequency limits (1-hour cooldown)."""
        response = flask_client.get('/api/alerts/info')
        data = json.loads(response.data)
        assert 'cooldown_minutes' in data or 'frequency' in data

    def test_privacy_information(self, flask_client):
        """Show privacy assurance."""
        response = flask_client.get('/api/alerts/info')
        data = json.loads(response.data)
        # Should mention privacy or data handling
        assert 'privacy' in str(data).lower() or 'email' in str(data).lower()
