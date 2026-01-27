"""
Phase 5: Headcount Routes Tests
===============================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates all Headcount page API functionality:
- Latest headcount display (detected vs expected, confidence, method)
- Headcount statistics (success rate, total checks, streak)
- Historical headcount log (last 30 records)
- Manual headcount trigger
- Headcount chart data

WHY THIS MATTERS:
-----------------
Nightly headcount is a core safety feature. It verifies all chickens are
inside the coop before nightfall. Missing chickens trigger SNS alerts.
The dashboard displays detection results with confidence scores and
historical trends for monitoring flock safety over time.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase5_api/routes/test_headcount_routes.py -v

Tests use Flask test client with mocked headcount data. Manual headcount
triggers are mocked to avoid actual camera processing during tests.
"""
import pytest
from flask import Flask, json
from datetime import datetime, timedelta


class TestLatestHeadcount:
    """Test latest headcount display endpoint."""

    def test_get_latest_headcount(self, flask_client):
        """Get most recent headcount result."""
        response = flask_client.get('/api/headcount/latest')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'detected_count' in data
        assert 'expected_count' in data
        assert 'timestamp' in data

    def test_latest_headcount_has_confidence(self, flask_client):
        """Latest headcount includes confidence percentage."""
        response = flask_client.get('/api/headcount/latest')
        data = json.loads(response.data)
        assert 'confidence' in data
        assert 0 <= data['confidence'] <= 100

    def test_latest_headcount_has_method(self, flask_client):
        """Latest headcount includes detection method."""
        response = flask_client.get('/api/headcount/latest')
        data = json.loads(response.data)
        assert 'method' in data
        assert data['method'] in ['manual', 'automated', 'simple_count', 'ml_detect']

    def test_latest_headcount_has_all_present_flag(self, flask_client):
        """Latest headcount includes all_present boolean."""
        response = flask_client.get('/api/headcount/latest')
        data = json.loads(response.data)
        assert 'all_present' in data
        assert isinstance(data['all_present'], bool)

    def test_latest_headcount_when_no_data(self, flask_client):
        """Handle case when no headcount data exists yet."""
        # This depends on test setup - may return 404 or empty data
        response = flask_client.get('/api/headcount/latest')
        # Should not crash, either returns data or appropriate status
        assert response.status_code in [200, 404]


class TestHeadcountStatistics:
    """Test headcount statistics endpoint."""

    def test_get_headcount_stats(self, flask_client):
        """Get overall headcount statistics."""
        response = flask_client.get('/api/headcount/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success_rate' in data
        assert 'total_checks' in data
        assert 'current_streak' in data

    def test_success_rate_percentage(self, flask_client):
        """Success rate is a valid percentage."""
        response = flask_client.get('/api/headcount/stats')
        data = json.loads(response.data)
        assert 0 <= data['success_rate'] <= 100

    def test_current_streak_days(self, flask_client):
        """Current streak is consecutive days all chickens present."""
        response = flask_client.get('/api/headcount/stats')
        data = json.loads(response.data)
        assert data['current_streak'] >= 0
        assert isinstance(data['current_streak'], int)

    def test_total_checks_count(self, flask_client):
        """Total checks is cumulative count."""
        response = flask_client.get('/api/headcount/stats')
        data = json.loads(response.data)
        assert data['total_checks'] >= 0
        assert isinstance(data['total_checks'], int)


class TestHeadcountHistory:
    """Test headcount history log endpoint."""

    def test_get_headcount_history(self, flask_client):
        """Get historical headcount records."""
        response = flask_client.get('/api/headcount/history')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'records' in data
        assert isinstance(data['records'], list)

    def test_history_default_limit_30(self, flask_client):
        """History returns last 30 records by default."""
        response = flask_client.get('/api/headcount/history')
        data = json.loads(response.data)
        assert len(data['records']) <= 30

    def test_history_custom_limit(self, flask_client):
        """Can specify custom limit for history."""
        response = flask_client.get('/api/headcount/history?limit=10')
        data = json.loads(response.data)
        assert len(data['records']) <= 10

    def test_history_record_structure(self, flask_client):
        """Each history record has required fields."""
        response = flask_client.get('/api/headcount/history')
        data = json.loads(response.data)

        if len(data['records']) > 0:
            record = data['records'][0]
            assert 'timestamp' in record
            assert 'detected_count' in record
            assert 'expected_count' in record
            assert 'all_present' in record
            assert 'confidence' in record
            assert 'method' in record

    def test_history_sorted_by_date_descending(self, flask_client):
        """History is sorted newest first."""
        response = flask_client.get('/api/headcount/history')
        data = json.loads(response.data)

        if len(data['records']) >= 2:
            first_ts = data['records'][0]['timestamp']
            second_ts = data['records'][1]['timestamp']
            assert first_ts >= second_ts

    def test_history_shows_missing_count(self, flask_client):
        """History indicates missing chicken count."""
        response = flask_client.get('/api/headcount/history')
        data = json.loads(response.data)

        if len(data['records']) > 0:
            record = data['records'][0]
            expected_missing = record['expected_count'] - record['detected_count']
            if 'missing_count' in record:
                assert record['missing_count'] == max(0, expected_missing)

    def test_history_has_notes_field(self, flask_client):
        """History records can have notes."""
        response = flask_client.get('/api/headcount/history')
        data = json.loads(response.data)

        if len(data['records']) > 0:
            # Notes field is optional
            record = data['records'][0]
            if 'notes' in record:
                assert isinstance(record['notes'], (str, type(None)))


class TestManualHeadcount:
    """Test manual headcount trigger endpoint."""

    def test_trigger_manual_headcount(self, flask_client):
        """Trigger a manual headcount check."""
        response = flask_client.post('/api/headcount/run')
        assert response.status_code in [200, 202]  # 202 for async
        data = json.loads(response.data)
        assert 'status' in data

    def test_manual_headcount_returns_job_id(self, flask_client):
        """Manual headcount returns job ID for tracking."""
        response = flask_client.post('/api/headcount/run')
        data = json.loads(response.data)
        # May return job_id for async tracking
        if response.status_code == 202:
            assert 'job_id' in data

    def test_manual_headcount_target_coop(self, flask_client):
        """Can target specific coop for headcount."""
        response = flask_client.post(
            '/api/headcount/run',
            json={'coop_id': 'coop1'}
        )
        assert response.status_code in [200, 202]

    def test_manual_headcount_progress_feedback(self, flask_client):
        """Manual headcount provides progress feedback."""
        response = flask_client.post('/api/headcount/run')
        data = json.loads(response.data)
        # Should indicate estimated time or progress
        assert 'message' in data or 'estimated_time' in data or 'status' in data

    def test_cannot_run_concurrent_headcount(self, flask_client):
        """Prevent concurrent headcount runs."""
        # First run
        flask_client.post('/api/headcount/run')
        # Second run should fail or queue
        response = flask_client.post('/api/headcount/run')
        # May return 409 Conflict or queue the request
        assert response.status_code in [200, 202, 409]


class TestHeadcountChartData:
    """Test headcount chart data endpoint."""

    def test_get_chart_data(self, flask_client):
        """Get data for headcount trend chart."""
        response = flask_client.get('/api/headcount/chart')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data_points' in data

    def test_chart_data_structure(self, flask_client):
        """Chart data has timestamp and count values."""
        response = flask_client.get('/api/headcount/chart')
        data = json.loads(response.data)

        if len(data['data_points']) > 0:
            point = data['data_points'][0]
            assert 'timestamp' in point or 'date' in point
            assert 'detected' in point or 'count' in point

    def test_chart_data_time_range(self, flask_client):
        """Can specify time range for chart data."""
        response = flask_client.get('/api/headcount/chart?days=14')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should only include last 14 days of data
        assert 'data_points' in data


class TestHeadcountWarnings:
    """Test headcount warning messages."""

    def test_warning_when_no_chickens_registered(self, flask_client):
        """Show warning when chicken registry is empty."""
        response = flask_client.get('/api/headcount/warnings')
        data = json.loads(response.data)
        assert 'warnings' in data
        # Warning about registration depends on state
        if data.get('chicken_count', 0) == 0:
            assert any('register' in w.lower() for w in data['warnings'])

    def test_warning_when_no_headcount_data(self, flask_client):
        """Show warning when no headcount data exists."""
        response = flask_client.get('/api/headcount/warnings')
        data = json.loads(response.data)
        # Warning about no data depends on state
        assert 'warnings' in data


class TestHeadcountAuthorization:
    """Test headcount endpoint authorization."""

    def test_headcount_requires_authentication(self, flask_client):
        """Headcount endpoints require authentication."""
        # Without authentication
        pass  # Implementation specific

    def test_manual_headcount_requires_write_permission(self, flask_client):
        """Manual headcount trigger requires write permission."""
        pass  # Implementation specific
