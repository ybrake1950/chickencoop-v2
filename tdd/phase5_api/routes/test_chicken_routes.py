"""
TDD Tests: Chicken Registry API Routes

These tests define the expected behavior for chicken management API endpoints.
Implement src/api/routes/chickens.py to make these tests pass.

Run: pytest tdd/phase5_api/routes/test_chicken_routes.py -v

FUNCTIONALITY BEING TESTED:
- GET /api/chickens - List all chickens
- POST /api/chickens - Register new chicken
- GET /api/chickens/<id> - Get single chicken details
- PUT /api/chickens/<id> - Update chicken details
- DELETE /api/chickens/<id> - Deactivate chicken
- GET /api/headcount/latest - Get latest headcount
- GET /api/headcount/history - Get headcount history
- POST /api/headcount/run - Trigger manual headcount

WHY THIS MATTERS:
The chicken registry tracks all chickens in each coop. The expected count is used
by the nightly headcount to detect missing chickens and trigger alerts.

HOW TESTS ARE EXECUTED:
1. Tests register chicken routes with Flask test app
2. Flask test client makes HTTP requests
3. Response status codes and JSON structure verified
4. Database operations are mocked
"""

import pytest
import json
from unittest.mock import MagicMock, patch


# =============================================================================
# Test: GET /api/chickens
# =============================================================================

class TestListChickens:
    """Tests for chicken listing endpoint."""

    def test_list_chickens_returns_200(self, flask_app, flask_client):
        """GET /api/chickens should return 200."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.get('/api/chickens')

        assert response.status_code == 200

    def test_list_chickens_returns_array(self, flask_app, flask_client):
        """Response should contain array of chickens."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.get('/api/chickens')
        data = response.get_json()

        assert "chickens" in data
        assert isinstance(data["chickens"], list)

    def test_list_chickens_includes_expected_count(self, flask_app, flask_client):
        """Response should include expected count."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.get_all_chickens') as mock_get:
            mock_get.return_value = [
                {"id": 1, "name": "Henrietta", "is_active": True},
                {"id": 2, "name": "Clover", "is_active": True},
            ]

            response = flask_client.get('/api/chickens')
            data = response.get_json()

        assert "expected_count" in data
        assert data["expected_count"] == 2

    def test_filter_active_only(self, flask_app, flask_client):
        """Should optionally filter to active chickens only."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.get('/api/chickens?active=true')

        assert response.status_code == 200


# =============================================================================
# Test: POST /api/chickens
# =============================================================================

class TestRegisterChicken:
    """Tests for chicken registration endpoint."""

    def test_register_chicken_returns_201(self, flask_app, flask_client):
        """POST /api/chickens should return 201."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.create_chicken') as mock_create:
            mock_create.return_value = {"id": 1, "name": "Henrietta"}

            response = flask_client.post('/api/chickens',
                json={
                    "name": "Henrietta",
                    "breed": "Rhode Island Red",
                    "color": "red"
                }
            )

        assert response.status_code in [200, 201]

    def test_register_requires_name(self, flask_app, flask_client):
        """Should require chicken name."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.post('/api/chickens',
            json={"breed": "Leghorn"}  # No name
        )

        assert response.status_code == 400

    def test_register_duplicate_name_fails(self, flask_app, flask_client):
        """Should reject duplicate chicken names."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.create_chicken') as mock_create:
            mock_create.side_effect = Exception("Duplicate name")

            response = flask_client.post('/api/chickens',
                json={"name": "Henrietta", "breed": "Leghorn"}
            )

        assert response.status_code in [400, 409]

    def test_register_returns_created_chicken(self, flask_app, flask_client):
        """Should return the created chicken data."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.create_chicken') as mock_create:
            mock_create.return_value = {
                "id": 1,
                "name": "Henrietta",
                "breed": "Rhode Island Red",
                "is_active": True
            }

            response = flask_client.post('/api/chickens',
                json={"name": "Henrietta", "breed": "Rhode Island Red"}
            )
            data = response.get_json()

        assert "id" in data
        assert data["name"] == "Henrietta"


# =============================================================================
# Test: PUT /api/chickens/<id>
# =============================================================================

class TestUpdateChicken:
    """Tests for chicken update endpoint."""

    def test_update_chicken_returns_200(self, flask_app, flask_client):
        """PUT /api/chickens/<id> should return 200."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.update_chicken') as mock_update:
            mock_update.return_value = {"id": 1, "name": "Henrietta Updated"}

            response = flask_client.put('/api/chickens/1',
                json={"name": "Henrietta Updated"}
            )

        assert response.status_code == 200

    def test_update_nonexistent_returns_404(self, flask_app, flask_client):
        """Should return 404 for non-existent chicken."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.update_chicken') as mock_update:
            mock_update.return_value = None

            response = flask_client.put('/api/chickens/99999',
                json={"name": "Ghost Chicken"}
            )

        assert response.status_code == 404


# =============================================================================
# Test: DELETE /api/chickens/<id>
# =============================================================================

class TestDeactivateChicken:
    """Tests for chicken deactivation endpoint."""

    def test_deactivate_chicken_returns_200(self, flask_app, flask_client):
        """DELETE /api/chickens/<id> should deactivate (not delete)."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.deactivate_chicken') as mock_deactivate:
            mock_deactivate.return_value = True

            response = flask_client.delete('/api/chickens/1')

        assert response.status_code in [200, 204]

    def test_deactivate_preserves_history(self, flask_app, flask_client):
        """Deactivation should preserve chicken for historical records."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.deactivate_chicken') as mock_deactivate:
            mock_deactivate.return_value = True

            response = flask_client.delete('/api/chickens/1')

        # Verify deactivate was called (not hard delete)
        mock_deactivate.assert_called_once()


# =============================================================================
# Test: GET /api/headcount/latest
# =============================================================================

class TestGetLatestHeadcount:
    """Tests for latest headcount endpoint."""

    def test_get_latest_returns_200(self, flask_app, flask_client):
        """GET /api/headcount/latest should return 200."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.get_latest_headcount') as mock_get:
            mock_get.return_value = {
                "timestamp": "2025-01-25T20:05:00Z",
                "count_detected": 6,
                "expected_count": 6,
                "all_present": True,
                "confidence": 0.92
            }

            response = flask_client.get('/api/headcount/latest')

        assert response.status_code == 200

    def test_get_latest_includes_required_fields(self, flask_app, flask_client):
        """Response should include count and status fields."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.get_latest_headcount') as mock_get:
            mock_get.return_value = {
                "count_detected": 5,
                "expected_count": 6,
                "all_present": False
            }

            response = flask_client.get('/api/headcount/latest')
            data = response.get_json()

        assert "count_detected" in data or "count" in data
        assert "expected_count" in data or "expected" in data
        assert "all_present" in data

    def test_get_latest_no_data_returns_empty(self, flask_app, flask_client):
        """Should handle no headcount data gracefully."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.get_latest_headcount') as mock_get:
            mock_get.return_value = None

            response = flask_client.get('/api/headcount/latest')

        assert response.status_code in [200, 204, 404]


# =============================================================================
# Test: GET /api/headcount/history
# =============================================================================

class TestGetHeadcountHistory:
    """Tests for headcount history endpoint."""

    def test_get_history_returns_200(self, flask_app, flask_client):
        """GET /api/headcount/history should return 200."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.get('/api/headcount/history')

        assert response.status_code == 200

    def test_get_history_with_days_param(self, flask_app, flask_client):
        """Should accept days parameter."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.get('/api/headcount/history?days=30')

        assert response.status_code == 200

    def test_get_history_returns_array(self, flask_app, flask_client):
        """Response should be array of headcount records."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.get_headcount_history') as mock_get:
            mock_get.return_value = [
                {"timestamp": "2025-01-25T20:00:00Z", "count_detected": 6},
                {"timestamp": "2025-01-24T20:00:00Z", "count_detected": 6},
            ]

            response = flask_client.get('/api/headcount/history')
            data = response.get_json()

        assert isinstance(data, list) or "history" in data


# =============================================================================
# Test: POST /api/headcount/run
# =============================================================================

class TestRunManualHeadcount:
    """Tests for manual headcount trigger endpoint."""

    def test_run_headcount_returns_202(self, flask_app, flask_client):
        """POST /api/headcount/run should return 202 (accepted)."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.trigger_headcount') as mock_trigger:
            mock_trigger.return_value = {"status": "started"}

            response = flask_client.post('/api/headcount/run')

        assert response.status_code in [200, 202]

    def test_run_headcount_returns_status(self, flask_app, flask_client):
        """Should return status message."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.chickens.trigger_headcount') as mock_trigger:
            mock_trigger.return_value = {"status": "started", "message": "Headcount initiated"}

            response = flask_client.post('/api/headcount/run')
            data = response.get_json()

        assert "status" in data or "message" in data

    def test_run_headcount_requires_auth(self, flask_app, flask_client):
        """Should require authentication."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.chickens import register_routes
        register_routes(flask_app)

        # No session
        response = flask_client.post('/api/headcount/run')

        assert response.status_code in [401, 302, 403]
