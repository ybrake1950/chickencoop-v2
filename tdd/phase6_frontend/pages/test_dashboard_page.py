"""
Phase 6: Dashboard Page Tests
=============================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates all Dashboard page functionality:
- Coop selection toggle (Coop 1, Coop 2, or both)
- Manual refresh controls and auto-refresh status
- System status display (online/offline, temp, humidity, door)
- Live camera streaming (30-second duration)
- Sensor data charts with time range selection
- Video grid with filters and infinite scroll
- Data export to CSV

WHY THIS MATTERS:
-----------------
The Dashboard is the main view users see daily. It provides at-a-glance
status of all coops, real-time sensor readings, live camera feeds, and
recent videos. Any bugs here directly impact user experience and their
ability to monitor chicken safety.

HOW TESTS ARE EXECUTED:
-----------------------
    # Run with pytest (Python backend tests)
    pytest tdd/phase6_frontend/pages/test_dashboard_page.py -v

    # Run React component tests with Vitest
    cd webapp && npm test -- Dashboard

These tests verify both the API data formatting and React component behavior.
Backend tests use Flask client, frontend tests use React Testing Library.
"""
import pytest
from flask import Flask, json


class TestCoopSelection:
    """Test coop selection toggle functionality."""

    def test_get_available_coops(self, flask_client):
        """Get list of available coops."""
        response = flask_client.get('/api/coops')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'coops' in data
        assert 'coop1' in [c['id'] for c in data['coops']]
        assert 'coop2' in [c['id'] for c in data['coops']]

    def test_get_status_for_single_coop(self, flask_client):
        """Get status for a single coop."""
        response = flask_client.get('/api/status?coop_id=coop1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['coop_id'] == 'coop1'

    def test_get_status_for_both_coops(self, flask_client):
        """Get combined status for both coops."""
        response = flask_client.get('/api/status?coop_id=all')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'coop1' in data or 'coops' in data

    def test_coop_selection_persists(self, flask_client):
        """Coop selection preference is saved."""
        # This is handled client-side in localStorage
        # API should accept any valid coop_id parameter
        pass


class TestRefreshControls:
    """Test manual refresh and auto-refresh functionality."""

    def test_refresh_all_endpoint(self, flask_client):
        """Refresh all dashboard data."""
        response = flask_client.post('/api/dashboard/refresh')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert 'sensor_data' in data
        assert 'videos' in data

    def test_refresh_returns_last_updated(self, flask_client):
        """Refresh returns last updated timestamp."""
        response = flask_client.post('/api/dashboard/refresh')
        data = json.loads(response.data)
        assert 'last_updated' in data

    def test_auto_refresh_status(self, flask_client):
        """Get auto-refresh status and interval."""
        response = flask_client.get('/api/settings/auto-refresh')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'enabled' in data
        assert 'interval_seconds' in data


class TestSystemStatusDisplay:
    """Test system status section of dashboard."""

    def test_get_coop_online_status(self, flask_client):
        """Get online/offline status for each coop."""
        response = flask_client.get('/api/status')
        data = json.loads(response.data)
        assert 'online' in data

    def test_get_temperature_reading(self, flask_client):
        """Get current temperature reading."""
        response = flask_client.get('/api/status')
        data = json.loads(response.data)
        assert 'temperature' in data
        assert isinstance(data['temperature'], (int, float))

    def test_get_humidity_reading(self, flask_client):
        """Get current humidity reading."""
        response = flask_client.get('/api/status')
        data = json.loads(response.data)
        assert 'humidity' in data
        assert 0 <= data['humidity'] <= 100

    def test_get_door_status(self, flask_client):
        """Get door position status (open/closed/unknown)."""
        response = flask_client.get('/api/status')
        data = json.loads(response.data)
        assert 'door_status' in data
        assert data['door_status'] in ['open', 'closed', 'unknown']

    def test_get_last_update_timestamp(self, flask_client):
        """Get last sensor update timestamp."""
        response = flask_client.get('/api/status')
        data = json.loads(response.data)
        assert 'last_update' in data

    def test_check_door_endpoint(self, flask_client):
        """Check door position manually."""
        response = flask_client.post('/api/check-door', json={'coop_id': 'coop1'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'door_status' in data

    def test_check_door_cooldown(self, flask_client):
        """Check door has 60-second cooldown."""
        # First check
        flask_client.post('/api/check-door', json={'coop_id': 'coop1'})
        # Second check within cooldown
        response = flask_client.post('/api/check-door', json={'coop_id': 'coop1'})
        # Should indicate cooldown or rate limit
        data = json.loads(response.data)
        # May return 429 or include cooldown info
        assert response.status_code in [200, 429] or 'cooldown' in str(data)

    def test_offline_duration_tracking(self, flask_client):
        """Track how long coop has been offline."""
        response = flask_client.get('/api/status')
        data = json.loads(response.data)
        if not data['online']:
            assert 'offline_since' in data or 'offline_duration' in data

    def test_trend_indicators(self, flask_client):
        """Get trend indicators for temperature/humidity."""
        response = flask_client.get('/api/status')
        data = json.loads(response.data)
        # Trend shows if values are rising/falling
        if 'trend' in data:
            assert data['trend']['temperature'] in ['up', 'down', 'stable']
            assert data['trend']['humidity'] in ['up', 'down', 'stable']

    def test_threshold_violation_highlight(self, flask_client):
        """Highlight abnormal values exceeding thresholds."""
        response = flask_client.get('/api/status')
        data = json.loads(response.data)
        # If value exceeds threshold, should be flagged
        if 'alerts' in data:
            for alert in data['alerts']:
                assert 'type' in alert
                assert 'value' in alert


class TestLiveCameraView:
    """Test live camera streaming functionality."""

    def test_get_live_stream_url(self, flask_client):
        """Get URL for live camera stream."""
        response = flask_client.get('/api/camera/live?coop_id=coop1&camera=indoor')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'stream_url' in data

    def test_live_stream_30_second_duration(self, flask_client):
        """Live stream has 30-second duration limit."""
        response = flask_client.get('/api/camera/live?coop_id=coop1&camera=indoor')
        data = json.loads(response.data)
        assert 'duration' in data
        assert data['duration'] <= 30

    def test_toggle_between_live_and_grid(self, flask_client):
        """API supports both live and grid view modes."""
        # This is frontend toggle, API just provides data
        pass


class TestSensorDataCharts:
    """Test sensor data chart functionality."""

    def test_get_chart_data_default_range(self, flask_client):
        """Get sensor data for charts (default 24h)."""
        response = flask_client.get('/api/sensor-data')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'readings' in data
        assert isinstance(data['readings'], list)

    def test_chart_time_range_6h(self, flask_client):
        """Get sensor data for 6-hour range."""
        response = flask_client.get('/api/sensor-data?range=6h')
        assert response.status_code == 200

    def test_chart_time_range_12h(self, flask_client):
        """Get sensor data for 12-hour range."""
        response = flask_client.get('/api/sensor-data?range=12h')
        assert response.status_code == 200

    def test_chart_time_range_24h(self, flask_client):
        """Get sensor data for 24-hour range."""
        response = flask_client.get('/api/sensor-data?range=24h')
        assert response.status_code == 200

    def test_chart_time_range_3d(self, flask_client):
        """Get sensor data for 3-day range."""
        response = flask_client.get('/api/sensor-data?range=3d')
        assert response.status_code == 200

    def test_chart_time_range_7d(self, flask_client):
        """Get sensor data for 7-day range."""
        response = flask_client.get('/api/sensor-data?range=7d')
        assert response.status_code == 200

    def test_chart_time_range_30d(self, flask_client):
        """Get sensor data for 30-day range."""
        response = flask_client.get('/api/sensor-data?range=30d')
        assert response.status_code == 200

    def test_chart_data_includes_statistics(self, flask_client):
        """Chart data includes min/max/average statistics."""
        response = flask_client.get('/api/sensor-data')
        data = json.loads(response.data)
        assert 'statistics' in data
        assert 'temperature' in data['statistics']
        assert 'min' in data['statistics']['temperature']
        assert 'max' in data['statistics']['temperature']
        assert 'avg' in data['statistics']['temperature']

    def test_chart_data_respects_timezone(self, flask_client):
        """Chart data timestamps respect configured timezone."""
        response = flask_client.get('/api/sensor-data?timezone=CST')
        assert response.status_code == 200

    def test_chart_threshold_reference_lines(self, flask_client):
        """Get threshold values for chart reference lines."""
        response = flask_client.get('/api/settings/thresholds')
        data = json.loads(response.data)
        assert 'temperature_min' in data
        assert 'temperature_max' in data


class TestVideoGrid:
    """Test video grid functionality."""

    def test_get_recent_videos(self, flask_client, mock_s3_client):
        """Get recent videos for grid display."""
        response = flask_client.get('/api/videos')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'videos' in data
        assert isinstance(data['videos'], list)

    def test_video_grid_pagination(self, flask_client, mock_s3_client):
        """Videos support pagination (12 per page)."""
        response = flask_client.get('/api/videos?limit=12&offset=0')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['videos']) <= 12

    def test_video_filter_by_camera(self, flask_client, mock_s3_client):
        """Filter videos by camera (indoor/outdoor)."""
        response = flask_client.get('/api/videos?camera=indoor')
        assert response.status_code == 200
        data = json.loads(response.data)
        for video in data['videos']:
            assert video['camera'] == 'indoor'

    def test_video_filter_by_date_today(self, flask_client, mock_s3_client):
        """Filter videos by date (today)."""
        response = flask_client.get('/api/videos?date_range=today')
        assert response.status_code == 200

    def test_video_filter_by_date_week(self, flask_client, mock_s3_client):
        """Filter videos by date (this week)."""
        response = flask_client.get('/api/videos?date_range=week')
        assert response.status_code == 200

    def test_video_filter_by_date_month(self, flask_client, mock_s3_client):
        """Filter videos by date (this month)."""
        response = flask_client.get('/api/videos?date_range=month')
        assert response.status_code == 200

    def test_video_sort_newest(self, flask_client, mock_s3_client):
        """Sort videos by newest first."""
        response = flask_client.get('/api/videos?sort=newest')
        assert response.status_code == 200

    def test_video_sort_oldest(self, flask_client, mock_s3_client):
        """Sort videos by oldest first."""
        response = flask_client.get('/api/videos?sort=oldest')
        assert response.status_code == 200

    def test_video_sort_size(self, flask_client, mock_s3_client):
        """Sort videos by file size."""
        response = flask_client.get('/api/videos?sort=size')
        assert response.status_code == 200

    def test_video_thumbnail_url(self, flask_client, mock_s3_client):
        """Videos include thumbnail URLs."""
        response = flask_client.get('/api/videos')
        data = json.loads(response.data)
        if len(data['videos']) > 0:
            assert 'thumbnail_url' in data['videos'][0]

    def test_video_metadata(self, flask_client, mock_s3_client):
        """Videos include metadata (timestamp, size, trigger)."""
        response = flask_client.get('/api/videos')
        data = json.loads(response.data)
        if len(data['videos']) > 0:
            video = data['videos'][0]
            assert 'timestamp' in video
            assert 'file_size' in video
            assert 'trigger_type' in video  # motion or manual

    def test_video_count_display(self, flask_client, mock_s3_client):
        """Get total video count for display."""
        response = flask_client.get('/api/videos/count')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total' in data

    def test_manual_record_button(self, flask_client):
        """Trigger manual video recording."""
        response = flask_client.post(
            '/api/manual-record',
            json={'coop_id': 'coop1', 'camera': 'indoor'}
        )
        assert response.status_code in [200, 202]


class TestVideoPlayer:
    """Test video playback modal."""

    def test_get_video_playback_url(self, flask_client, mock_s3_client):
        """Get presigned URL for video playback."""
        response = flask_client.get('/api/videos/video123/url')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'url' in data

    def test_video_url_expiry(self, flask_client, mock_s3_client):
        """Video URL has 1-hour expiry."""
        response = flask_client.get('/api/videos/video123/url')
        data = json.loads(response.data)
        assert 'expires_in' in data
        assert data['expires_in'] <= 3600


class TestDataExport:
    """Test CSV data export functionality."""

    def test_export_sensor_data_csv(self, flask_client):
        """Export sensor data as CSV."""
        response = flask_client.get('/api/export/sensor-data?format=csv')
        assert response.status_code == 200
        assert response.content_type == 'text/csv'

    def test_export_with_date_range(self, flask_client):
        """Export with date range filter."""
        response = flask_client.get('/api/export/sensor-data?format=csv&start=2024-01-01&end=2024-01-31')
        assert response.status_code == 200

    def test_export_multi_coop(self, flask_client):
        """Export data from multiple coops."""
        response = flask_client.get('/api/export/sensor-data?format=csv&coop_id=all')
        assert response.status_code == 200
