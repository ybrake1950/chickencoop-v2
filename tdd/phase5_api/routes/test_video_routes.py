"""
TDD Tests: Video API Routes

These tests define the expected behavior for video management API endpoints.
Implement src/api/routes/videos.py to make these tests pass.

Run: pytest tdd/phase5_api/routes/test_video_routes.py -v

FUNCTIONALITY BEING TESTED:
- GET /api/videos - List all videos
- GET /api/videos/<id> - Get single video details
- POST /api/videos/retain - Mark video for permanent retention
- DELETE /api/videos/<id> - Delete a video
- Video filtering by camera, date, retention status
- Presigned URL generation for playback
- Thumbnail URL generation

WHY THIS MATTERS:
The video API serves the dashboard's video browser. Users can view motion-triggered
recordings, mark important videos for retention, and delete unwanted ones.

HOW TESTS ARE EXECUTED:
1. Tests register video routes with Flask test app
2. Flask test client makes HTTP requests
3. Response status codes and JSON structure verified
4. Authentication is simulated via session
"""

import pytest
import json
from unittest.mock import MagicMock, patch


# =============================================================================
# Test: GET /api/videos
# =============================================================================

class TestListVideos:
    """Tests for video listing endpoint."""

    def test_list_videos_returns_200(self, flask_app, flask_client):
        """GET /api/videos should return 200."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.get('/api/videos')

        assert response.status_code == 200

    def test_list_videos_returns_json(self, flask_app, flask_client):
        """Response should be JSON."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.get('/api/videos')
        data = response.get_json()

        assert data is not None
        assert "videos" in data

    def test_list_videos_contains_expected_fields(self, flask_app, flask_client):
        """Each video should have required fields."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        # Mock video data
        with patch('src.api.routes.videos.get_videos') as mock_get:
            mock_get.return_value = [{
                "id": 1,
                "filename": "motion_20250125.mp4",
                "s3_key": "videos/coop1/motion_20250125.mp4",
                "camera": "indoor",
                "upload_date": "2025-01-25T14:30:00Z",
                "url": "https://presigned.url",
                "thumbnail_url": "https://thumbnail.url",
                "retain_permanently": False
            }]

            response = flask_client.get('/api/videos')
            data = response.get_json()

        if data["videos"]:
            video = data["videos"][0]
            assert "filename" in video
            assert "camera" in video
            assert "url" in video or "presigned_url" in video

    def test_list_videos_requires_auth(self, flask_app, flask_client):
        """Should require authentication."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        # No session
        response = flask_client.get('/api/videos')

        assert response.status_code in [401, 302, 403]


# =============================================================================
# Test: Video Filtering
# =============================================================================

class TestVideoFiltering:
    """Tests for video filtering options."""

    def test_filter_by_camera(self, flask_app, flask_client):
        """Should filter videos by camera."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.get('/api/videos?camera=indoor')

        assert response.status_code == 200

    def test_filter_by_date(self, flask_app, flask_client):
        """Should filter videos by date range."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.get('/api/videos?start_date=2025-01-25&end_date=2025-01-26')

        assert response.status_code == 200

    def test_filter_retained_only(self, flask_app, flask_client):
        """Should filter to retained videos only."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.get('/api/videos?retained=true')

        assert response.status_code == 200

    def test_pagination_support(self, flask_app, flask_client):
        """Should support pagination."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.get('/api/videos?page=1&per_page=10')

        assert response.status_code == 200
        data = response.get_json()
        assert "total" in data or "page" in data or "videos" in data


# =============================================================================
# Test: POST /api/videos/retain
# =============================================================================

class TestRetainVideo:
    """Tests for video retention endpoint."""

    def test_retain_video_returns_200(self, flask_app, flask_client):
        """POST /api/videos/retain should return 200."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.videos.retain_video') as mock_retain:
            mock_retain.return_value = True

            response = flask_client.post('/api/videos/retain',
                json={"s3_key": "videos/test.mp4", "note": "Important"}
            )

        assert response.status_code in [200, 201]

    def test_retain_requires_s3_key(self, flask_app, flask_client):
        """Should require s3_key in request."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        response = flask_client.post('/api/videos/retain',
            json={"note": "No key provided"}
        )

        assert response.status_code == 400

    def test_retain_stores_user_id(self, flask_app, flask_client):
        """Should record which user marked for retention."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 42

        with patch('src.api.routes.videos.retain_video') as mock_retain:
            mock_retain.return_value = True

            response = flask_client.post('/api/videos/retain',
                json={"s3_key": "videos/test.mp4"}
            )

            # Verify user_id was passed
            mock_retain.assert_called_once()
            call_kwargs = mock_retain.call_args.kwargs
            assert call_kwargs.get('user_id') == 42 or 42 in mock_retain.call_args[0]


# =============================================================================
# Test: DELETE /api/videos/<id>
# =============================================================================

class TestDeleteVideo:
    """Tests for video deletion endpoint."""

    def test_delete_video_returns_200(self, flask_app, flask_client):
        """DELETE /api/videos/<id> should return 200."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.videos.delete_video') as mock_delete:
            mock_delete.return_value = True

            response = flask_client.delete('/api/videos/1')

        assert response.status_code in [200, 204]

    def test_delete_nonexistent_returns_404(self, flask_app, flask_client):
        """Should return 404 for non-existent video."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.videos.delete_video') as mock_delete:
            mock_delete.return_value = False

            response = flask_client.delete('/api/videos/99999')

        assert response.status_code == 404

    def test_cannot_delete_retained_video(self, flask_app, flask_client):
        """Should prevent deletion of retained videos."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.videos.delete_video') as mock_delete:
            mock_delete.side_effect = Exception("Cannot delete retained video")

            response = flask_client.delete('/api/videos/1')

        assert response.status_code in [400, 403, 409]


# =============================================================================
# Test: GET /api/videos/<id>
# =============================================================================

class TestGetSingleVideo:
    """Tests for single video retrieval."""

    def test_get_video_returns_200(self, flask_app, flask_client):
        """GET /api/videos/<id> should return 200."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.videos.get_video_by_id') as mock_get:
            mock_get.return_value = {
                "id": 1,
                "filename": "test.mp4",
                "url": "https://presigned.url"
            }

            response = flask_client.get('/api/videos/1')

        assert response.status_code == 200

    def test_get_video_includes_presigned_url(self, flask_app, flask_client):
        """Response should include presigned URL for playback."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.videos.get_video_by_id') as mock_get:
            mock_get.return_value = {
                "id": 1,
                "filename": "test.mp4",
                "url": "https://s3.amazonaws.com/presigned"
            }

            response = flask_client.get('/api/videos/1')
            data = response.get_json()

        assert "url" in data or "presigned_url" in data

    def test_get_nonexistent_returns_404(self, flask_app, flask_client):
        """Should return 404 for non-existent video."""
        if flask_app is None:
            pytest.skip("Flask not available")

        from src.api.routes.videos import register_routes
        register_routes(flask_app)

        with flask_client.session_transaction() as sess:
            sess['user_id'] = 1

        with patch('src.api.routes.videos.get_video_by_id') as mock_get:
            mock_get.return_value = None

            response = flask_client.get('/api/videos/99999')

        assert response.status_code == 404
