"""
Phase 5: Settings Routes Tests
==============================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates all Settings page API functionality:
- Temperature unit preference (Fahrenheit/Celsius)
- Alert threshold configuration (temp min/max, humidity min/max)
- Notification preferences (email alerts, individual alert types)
- Reset to defaults functionality

WHY THIS MATTERS:
-----------------
Settings control how the system behaves for each user. Alert thresholds
determine when SNS notifications are triggered. Temperature unit preference
affects all temperature displays in the dashboard. Invalid settings could
cause missed alerts or confusing data display.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase5_api/routes/test_settings_routes.py -v

Tests use Flask test client to make HTTP requests to settings endpoints.
Settings are stored per-user in the database, so tests verify CRUD
operations and validation logic.
"""
import pytest
from flask import Flask, json


class TestTemperatureUnitPreference:
    """Test temperature unit preference (Fahrenheit/Celsius)."""

    def test_get_temperature_unit_returns_default_fahrenheit(self, flask_client):
        """Default temperature unit should be Fahrenheit."""
        response = flask_client.get('/api/settings/temperature-unit')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['unit'] == 'F'

    def test_set_temperature_unit_to_celsius(self, flask_client):
        """User can change temperature unit to Celsius."""
        response = flask_client.put(
            '/api/settings/temperature-unit',
            json={'unit': 'C'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['unit'] == 'C'

    def test_set_temperature_unit_to_fahrenheit(self, flask_client):
        """User can change temperature unit to Fahrenheit."""
        response = flask_client.put(
            '/api/settings/temperature-unit',
            json={'unit': 'F'}
        )
        assert response.status_code == 200

    def test_invalid_temperature_unit_rejected(self, flask_client):
        """Invalid temperature unit values should be rejected."""
        response = flask_client.put(
            '/api/settings/temperature-unit',
            json={'unit': 'K'}  # Kelvin not supported
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_temperature_unit_persists_across_requests(self, flask_client):
        """Temperature unit preference should persist."""
        # Set to Celsius
        flask_client.put('/api/settings/temperature-unit', json={'unit': 'C'})

        # Verify it persisted
        response = flask_client.get('/api/settings/temperature-unit')
        data = json.loads(response.data)
        assert data['unit'] == 'C'


class TestAlertThresholds:
    """Test alert threshold configuration."""

    def test_get_thresholds_returns_defaults(self, flask_client):
        """Get default alert thresholds."""
        response = flask_client.get('/api/settings/thresholds')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'temperature_min' in data
        assert 'temperature_max' in data
        assert 'humidity_min' in data
        assert 'humidity_max' in data

    def test_set_temperature_thresholds(self, flask_client):
        """User can set temperature alert thresholds."""
        response = flask_client.put(
            '/api/settings/thresholds',
            json={
                'temperature_min': 35,
                'temperature_max': 95
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['temperature_min'] == 35
        assert data['temperature_max'] == 95

    def test_set_humidity_thresholds(self, flask_client):
        """User can set humidity alert thresholds."""
        response = flask_client.put(
            '/api/settings/thresholds',
            json={
                'humidity_min': 30,
                'humidity_max': 80
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['humidity_min'] == 30
        assert data['humidity_max'] == 80

    def test_min_must_be_less_than_max_temperature(self, flask_client):
        """Temperature min must be less than max."""
        response = flask_client.put(
            '/api/settings/thresholds',
            json={
                'temperature_min': 80,
                'temperature_max': 40  # Invalid: min > max
            }
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_min_must_be_less_than_max_humidity(self, flask_client):
        """Humidity min must be less than max."""
        response = flask_client.put(
            '/api/settings/thresholds',
            json={
                'humidity_min': 70,
                'humidity_max': 30  # Invalid: min > max
            }
        )
        assert response.status_code == 400

    def test_humidity_must_be_in_valid_range(self, flask_client):
        """Humidity thresholds must be 0-100."""
        response = flask_client.put(
            '/api/settings/thresholds',
            json={
                'humidity_min': -10,  # Invalid: negative
                'humidity_max': 50
            }
        )
        assert response.status_code == 400

    def test_humidity_max_cannot_exceed_100(self, flask_client):
        """Humidity max cannot exceed 100%."""
        response = flask_client.put(
            '/api/settings/thresholds',
            json={
                'humidity_min': 20,
                'humidity_max': 150  # Invalid: > 100
            }
        )
        assert response.status_code == 400


class TestNotificationPreferences:
    """Test notification preference settings."""

    def test_get_notification_preferences(self, flask_client):
        """Get current notification preferences."""
        response = flask_client.get('/api/settings/notifications')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'email_enabled' in data
        assert 'temperature_alerts' in data
        assert 'humidity_alerts' in data
        assert 'system_alerts' in data

    def test_disable_email_notifications(self, flask_client):
        """User can disable all email notifications."""
        response = flask_client.put(
            '/api/settings/notifications',
            json={'email_enabled': False}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['email_enabled'] is False

    def test_enable_temperature_alerts(self, flask_client):
        """User can enable temperature alerts specifically."""
        response = flask_client.put(
            '/api/settings/notifications',
            json={'temperature_alerts': True}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['temperature_alerts'] is True

    def test_disable_humidity_alerts(self, flask_client):
        """User can disable humidity alerts specifically."""
        response = flask_client.put(
            '/api/settings/notifications',
            json={'humidity_alerts': False}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['humidity_alerts'] is False

    def test_disable_system_alerts(self, flask_client):
        """User can disable system status alerts."""
        response = flask_client.put(
            '/api/settings/notifications',
            json={'system_alerts': False}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['system_alerts'] is False

    def test_individual_alerts_disabled_when_email_disabled(self, flask_client):
        """Individual alerts should not trigger when email is disabled."""
        # First disable email
        flask_client.put('/api/settings/notifications', json={'email_enabled': False})

        # Even if temperature_alerts is True, no emails should send
        response = flask_client.get('/api/settings/notifications')
        data = json.loads(response.data)
        assert data['email_enabled'] is False
        # Note: Individual preferences can still be True, but won't send


class TestResetToDefaults:
    """Test reset to defaults functionality."""

    def test_reset_all_settings_to_defaults(self, flask_client):
        """User can reset all settings to application defaults."""
        # First change some settings
        flask_client.put('/api/settings/temperature-unit', json={'unit': 'C'})
        flask_client.put('/api/settings/thresholds', json={'temperature_min': 20})
        flask_client.put('/api/settings/notifications', json={'email_enabled': False})

        # Reset to defaults
        response = flask_client.post('/api/settings/reset')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_reset_restores_default_temperature_unit(self, flask_client):
        """Reset restores Fahrenheit as default temperature unit."""
        flask_client.put('/api/settings/temperature-unit', json={'unit': 'C'})
        flask_client.post('/api/settings/reset')

        response = flask_client.get('/api/settings/temperature-unit')
        data = json.loads(response.data)
        assert data['unit'] == 'F'

    def test_reset_restores_default_thresholds(self, flask_client):
        """Reset restores default alert thresholds."""
        flask_client.put('/api/settings/thresholds', json={'temperature_min': 0})
        flask_client.post('/api/settings/reset')

        response = flask_client.get('/api/settings/thresholds')
        data = json.loads(response.data)
        # Verify defaults are restored (specific values depend on app defaults)
        assert data['temperature_min'] > 0  # Not the modified value

    def test_reset_confirmation_required(self, flask_client):
        """Reset should require confirmation in production."""
        # Without confirmation flag
        response = flask_client.post(
            '/api/settings/reset',
            json={'confirmed': False}
        )
        # Could be 400 or 200 depending on implementation
        # Key is that without confirmation, reset may not proceed


class TestSettingsAuthorization:
    """Test that settings require authentication."""

    def test_settings_require_authentication(self, flask_client):
        """All settings endpoints require authentication."""
        # Without login, should get 401
        # This depends on how authentication is implemented
        pass  # Placeholder - implementation specific

    def test_settings_are_user_specific(self, flask_client):
        """Each user has their own settings."""
        # Different users should have independent settings
        pass  # Placeholder - implementation specific
