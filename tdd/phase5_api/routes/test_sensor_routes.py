"""
TDD Tests: Sensor API Routes

These tests define the expected behavior for sensor data API endpoints.
Implement src/api/routes/sensors.py to make these tests pass.

Run: pytest tdd/phase5_api/routes/test_sensor_routes.py -v
"""

import pytest
import json
from unittest.mock import MagicMock, patch


# =============================================================================
# Test: GET /api/status
# =============================================================================

class TestStatusEndpoint:
    """Tests for the status endpoint."""

    def test_status_returns_200(self, flask_app, flask_client):
        """GET /api/status should return 200."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        response = flask_client.get('/api/status')

        assert response.status_code == 200

    def test_status_returns_json(self, flask_app, flask_client):
        """Status should return JSON."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        response = flask_client.get('/api/status')
        data = response.get_json()

        assert data is not None
        assert isinstance(data, dict)

    def test_status_contains_temperature(self, flask_app, flask_client):
        """Status should contain temperature."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        response = flask_client.get('/api/status')
        data = response.get_json()

        assert "temperature" in data or "temp" in data

    def test_status_contains_humidity(self, flask_app, flask_client):
        """Status should contain humidity."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        response = flask_client.get('/api/status')
        data = response.get_json()

        assert "humidity" in data

    def test_status_contains_timestamp(self, flask_app, flask_client):
        """Status should contain last update timestamp."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        response = flask_client.get('/api/status')
        data = response.get_json()

        assert "last_update" in data or "timestamp" in data


# =============================================================================
# Test: GET /api/sensor-data
# =============================================================================

class TestSensorDataEndpoint:
    """Tests for the sensor data endpoint."""

    def test_sensor_data_returns_200(self, flask_app, flask_client):
        """GET /api/sensor-data should return 200."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        response = flask_client.get('/api/sensor-data')

        assert response.status_code == 200

    def test_sensor_data_returns_list(self, flask_app, flask_client):
        """Sensor data should return list of readings."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        response = flask_client.get('/api/sensor-data')
        data = response.get_json()

        assert "data" in data
        assert isinstance(data["data"], list)

    def test_sensor_data_with_time_range(self, flask_app, flask_client):
        """Should filter by time range."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        response = flask_client.get('/api/sensor-data?range=24h')
        data = response.get_json()

        assert response.status_code == 200

    def test_sensor_data_with_coop_filter(self, flask_app, flask_client):
        """Should filter by coop ID."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        response = flask_client.get('/api/sensor-data?coop=coop1')
        data = response.get_json()

        assert response.status_code == 200


# =============================================================================
# Test: GET /api/alerts
# =============================================================================

class TestAlertsEndpoint:
    """Tests for the alerts endpoint."""

    def test_alerts_returns_200(self, flask_app, flask_client):
        """GET /api/alerts should return 200."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        response = flask_client.get('/api/alerts')

        assert response.status_code == 200

    def test_alerts_returns_list(self, flask_app, flask_client):
        """Alerts should return list."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        response = flask_client.get('/api/alerts')
        data = response.get_json()

        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_alert_structure(self, flask_app, flask_client):
        """Each alert should have type, message, timestamp."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        # Mock an alert
        with patch('src.api.routes.sensors.get_alerts') as mock_alerts:
            mock_alerts.return_value = [{
                "type": "temperature",
                "message": "High temperature: 95°F",
                "timestamp": "2025-01-25T14:30:00Z"
            }]

            response = flask_client.get('/api/alerts')
            data = response.get_json()

        if data["alerts"]:
            alert = data["alerts"][0]
            assert "type" in alert
            assert "message" in alert
            assert "timestamp" in alert


# =============================================================================
# Test: GET /api/download-csv
# =============================================================================

class TestCSVDownloadEndpoint:
    """Tests for CSV download endpoint."""

    def test_csv_download_returns_file(self, flask_app, flask_client):
        """GET /api/download-csv should return CSV file."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        # Requires authentication
        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.get('/api/download-csv')

        # Should return file or require auth
        assert response.status_code in [200, 401, 302]

    def test_csv_has_correct_content_type(self, flask_app, flask_client):
        """CSV response should have text/csv content type."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.sensors import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.get('/api/download-csv')

        if response.status_code == 200:
            assert 'text/csv' in response.content_type or 'application' in response.content_type
