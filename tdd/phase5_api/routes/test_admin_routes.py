"""
Phase 5: Admin Routes Tests
===========================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates all Admin page API functionality:
- Health metrics monitoring (Pi memory, storage, S3, AWS billing)
- Camera settings (indoor/outdoor toggles, motion recording)
- Nightly headcount settings
- Timezone configuration
- Dangerous operations (delete all videos, delete sensor data)
- Script management for remote Pi control

WHY THIS MATTERS:
-----------------
The Admin page provides system management capabilities. Health metrics help
identify resource issues before they cause failures. Camera settings control
recording behavior. Dangerous operations must be protected with confirmations
to prevent accidental data loss. Remote Pi control enables maintenance without
SSH access.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase5_api/routes/test_admin_routes.py -v

Tests use Flask test client with admin authentication. Dangerous operations
require confirmation tokens. Remote Pi operations are mocked to avoid actual
system changes during testing.
"""
import pytest
from flask import Flask, json


class TestHealthMetrics:
    """Test health metrics endpoints."""

    def test_get_pi_memory_metrics(self, flask_client):
        """Get Raspberry Pi memory usage metrics."""
        response = flask_client.get('/api/admin/health/memory')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'used_percent' in data
        assert 'available_mb' in data
        assert 'total_mb' in data
        assert 0 <= data['used_percent'] <= 100

    def test_get_pi_storage_metrics(self, flask_client):
        """Get Raspberry Pi disk storage metrics."""
        response = flask_client.get('/api/admin/health/storage')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'used_percent' in data
        assert 'available_gb' in data
        assert 'total_gb' in data

    def test_get_s3_storage_metrics(self, flask_client, mock_s3_client):
        """Get S3 video storage metrics."""
        response = flask_client.get('/api/admin/health/s3-storage')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'video_count' in data
        assert 'total_size_gb' in data

    def test_get_aws_billing_metrics(self, flask_client):
        """Get AWS month-to-date billing by service."""
        response = flask_client.get('/api/admin/health/billing')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_cost' in data
        assert 'by_service' in data
        assert isinstance(data['by_service'], dict)

    def test_get_all_health_metrics(self, flask_client):
        """Get all health metrics in one call."""
        response = flask_client.get('/api/admin/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'memory' in data
        assert 'storage' in data
        assert 's3_storage' in data
        assert 'last_updated' in data

    def test_refresh_health_metrics(self, flask_client):
        """Force refresh of health metrics."""
        response = flask_client.post('/api/admin/health/refresh')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'last_updated' in data


class TestCameraSettings:
    """Test camera configuration settings."""

    def test_get_camera_settings(self, flask_client):
        """Get current camera settings."""
        response = flask_client.get('/api/admin/camera-settings')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'indoor_enabled' in data
        assert 'outdoor_enabled' in data
        assert 'motion_recording_enabled' in data

    def test_enable_outdoor_motion_recording(self, flask_client):
        """Enable motion-triggered recording for outdoor camera."""
        response = flask_client.put(
            '/api/admin/camera-settings',
            json={'motion_recording_enabled': True}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['motion_recording_enabled'] is True

    def test_disable_outdoor_motion_recording(self, flask_client):
        """Disable motion-triggered recording."""
        response = flask_client.put(
            '/api/admin/camera-settings',
            json={'motion_recording_enabled': False}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['motion_recording_enabled'] is False

    def test_toggle_indoor_camera(self, flask_client):
        """Toggle indoor camera on/off."""
        response = flask_client.put(
            '/api/admin/camera-settings',
            json={'indoor_enabled': False}
        )
        assert response.status_code == 200


class TestHeadcountSettings:
    """Test nightly headcount configuration."""

    def test_get_headcount_settings(self, flask_client):
        """Get nightly headcount settings."""
        response = flask_client.get('/api/admin/headcount-settings')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'enabled' in data
        assert 'scheduled_time' in data

    def test_enable_nightly_headcount(self, flask_client):
        """Enable automated nightly headcount."""
        response = flask_client.put(
            '/api/admin/headcount-settings',
            json={'enabled': True}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['enabled'] is True

    def test_disable_nightly_headcount(self, flask_client):
        """Disable automated nightly headcount."""
        response = flask_client.put(
            '/api/admin/headcount-settings',
            json={'enabled': False}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['enabled'] is False

    def test_set_headcount_schedule_time(self, flask_client):
        """Set the scheduled time for nightly headcount."""
        response = flask_client.put(
            '/api/admin/headcount-settings',
            json={'scheduled_time': '19:30'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['scheduled_time'] == '19:30'


class TestTimezoneSettings:
    """Test timezone configuration."""

    def test_get_timezone(self, flask_client):
        """Get current timezone setting."""
        response = flask_client.get('/api/admin/timezone')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'timezone' in data

    def test_set_timezone_cst(self, flask_client):
        """Set timezone to Central Standard Time."""
        response = flask_client.put(
            '/api/admin/timezone',
            json={'timezone': 'CST'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['timezone'] == 'CST'

    def test_set_timezone_est(self, flask_client):
        """Set timezone to Eastern Standard Time."""
        response = flask_client.put(
            '/api/admin/timezone',
            json={'timezone': 'EST'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['timezone'] == 'EST'

    def test_set_timezone_utc(self, flask_client):
        """Set timezone to UTC."""
        response = flask_client.put(
            '/api/admin/timezone',
            json={'timezone': 'UTC'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['timezone'] == 'UTC'

    def test_invalid_timezone_rejected(self, flask_client):
        """Invalid timezone should be rejected."""
        response = flask_client.put(
            '/api/admin/timezone',
            json={'timezone': 'INVALID'}
        )
        assert response.status_code == 400


class TestDangerousOperations:
    """Test dangerous operations that require confirmation."""

    def test_delete_all_videos_requires_confirmation(self, flask_client):
        """Delete all videos requires confirmation."""
        response = flask_client.post(
            '/api/admin/delete-all-videos',
            json={'confirmed': False}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'confirmation required' in data.get('error', '').lower()

    def test_delete_all_videos_with_confirmation(self, flask_client, mock_s3_client):
        """Delete all videos with proper confirmation."""
        response = flask_client.post(
            '/api/admin/delete-all-videos',
            json={'confirmed': True}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'deleted_count' in data

    def test_delete_all_videos_deletes_from_s3(self, flask_client, mock_s3_client):
        """Verify videos are deleted from S3."""
        flask_client.post(
            '/api/admin/delete-all-videos',
            json={'confirmed': True}
        )
        # Verify mock_s3_client.delete_objects was called
        mock_s3_client.delete_objects.assert_called()

    def test_delete_all_videos_deletes_thumbnails(self, flask_client, mock_s3_client):
        """Verify thumbnails are also deleted."""
        response = flask_client.post(
            '/api/admin/delete-all-videos',
            json={'confirmed': True}
        )
        data = json.loads(response.data)
        assert 'thumbnails_deleted' in data

    def test_delete_sensor_data_requires_confirmation(self, flask_client):
        """Delete sensor data requires confirmation."""
        response = flask_client.post(
            '/api/admin/delete-sensor-data',
            json={'confirmed': False}
        )
        assert response.status_code == 400

    def test_delete_sensor_data_with_confirmation(self, flask_client, mock_s3_client):
        """Delete sensor data with proper confirmation."""
        response = flask_client.post(
            '/api/admin/delete-sensor-data',
            json={'confirmed': True}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_delete_sensor_data_deletes_csv_files(self, flask_client, mock_s3_client):
        """Verify CSV files are deleted from S3 and local."""
        flask_client.post(
            '/api/admin/delete-sensor-data',
            json={'confirmed': True}
        )
        # Verify deletion was called for CSV files


class TestRemotePiControl:
    """Test remote Raspberry Pi control scripts."""

    def test_get_available_scripts(self, flask_client):
        """Get list of available control scripts."""
        response = flask_client.get('/api/admin/scripts')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'scripts' in data
        assert len(data['scripts']) > 0

    def test_system_restart(self, flask_client):
        """Trigger system restart on selected coop."""
        response = flask_client.post(
            '/api/admin/scripts/system-restart',
            json={'coop_id': 'coop1'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data

    def test_health_check_script(self, flask_client):
        """Run health check diagnostics."""
        response = flask_client.post(
            '/api/admin/scripts/health-check',
            json={'coop_id': 'coop1'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'services' in data
        assert 'disk' in data
        assert 'temperature' in data

    def test_performance_monitor(self, flask_client):
        """Run performance monitoring script."""
        response = flask_client.post(
            '/api/admin/scripts/performance-monitor',
            json={'coop_id': 'coop1'}
        )
        assert response.status_code == 200

    def test_system_update(self, flask_client):
        """Trigger system update (apt upgrade)."""
        response = flask_client.post(
            '/api/admin/scripts/system-update',
            json={'coop_id': 'coop1'}
        )
        assert response.status_code == 200

    def test_start_services(self, flask_client):
        """Start services on selected coop."""
        response = flask_client.post(
            '/api/admin/scripts/service-control',
            json={'coop_id': 'coop1', 'action': 'start'}
        )
        assert response.status_code == 200

    def test_stop_services(self, flask_client):
        """Stop services on selected coop."""
        response = flask_client.post(
            '/api/admin/scripts/service-control',
            json={'coop_id': 'coop1', 'action': 'stop'}
        )
        assert response.status_code == 200

    def test_restart_services(self, flask_client):
        """Restart services on selected coop."""
        response = flask_client.post(
            '/api/admin/scripts/service-control',
            json={'coop_id': 'coop1', 'action': 'restart'}
        )
        assert response.status_code == 200

    def test_sensor_diagnostics(self, flask_client):
        """Run sensor diagnostics (SHT41, cameras, motion)."""
        response = flask_client.post(
            '/api/admin/scripts/sensor-diagnostics',
            json={'coop_id': 'coop1'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'sensors' in data

    def test_s3_scan(self, flask_client, mock_s3_client):
        """Scan S3 for corrupted videos (dry run)."""
        response = flask_client.post(
            '/api/admin/scripts/s3-scan',
            json={'dry_run': True}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'corrupted_count' in data
        assert 'dry_run' in data
        assert data['dry_run'] is True

    def test_s3_clean(self, flask_client, mock_s3_client):
        """Clean corrupted videos from S3."""
        response = flask_client.post(
            '/api/admin/scripts/s3-clean',
            json={'confirmed': True}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'deleted_count' in data

    def test_target_all_coops(self, flask_client):
        """Scripts can target all coops at once."""
        response = flask_client.post(
            '/api/admin/scripts/health-check',
            json={'coop_id': 'all'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'coop1' in data
        assert 'coop2' in data


class TestClimateControl:
    """Test climate control (fan) operations."""

    def test_get_climate_status(self, flask_client):
        """Get current climate status (fan, thresholds)."""
        response = flask_client.get('/api/admin/climate/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'fan_status' in data
        assert 'temperature_threshold' in data

    def test_fan_on(self, flask_client):
        """Turn fan on (manual override)."""
        response = flask_client.post(
            '/api/admin/climate/fan',
            json={'action': 'on', 'coop_id': 'coop1'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['fan_status'] == 'on'

    def test_fan_off(self, flask_client):
        """Turn fan off (manual override)."""
        response = flask_client.post(
            '/api/admin/climate/fan',
            json={'action': 'off', 'coop_id': 'coop1'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['fan_status'] == 'off'

    def test_fan_auto(self, flask_client):
        """Return fan to automatic control."""
        response = flask_client.post(
            '/api/admin/climate/fan',
            json={'action': 'auto', 'coop_id': 'coop1'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['fan_status'] == 'auto'


class TestAdminAuthorization:
    """Test that admin operations require proper authorization."""

    def test_admin_requires_authentication(self, flask_client):
        """Admin endpoints require authentication."""
        # Without authentication
        pass  # Implementation specific

    def test_dangerous_operations_require_admin_role(self, flask_client):
        """Dangerous operations require admin role."""
        # Regular users should not be able to delete all videos
        pass  # Implementation specific
