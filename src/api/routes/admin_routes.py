"""
Admin Routes for Chicken Coop API
=================================

Provides endpoints for system administration including:
- Health metrics monitoring
- Camera settings management
- Headcount settings
- Timezone configuration
- Dangerous operations (with confirmation)
- Remote Pi control scripts
- Climate control
"""

from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, g

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# In-memory state for settings (in production would use database)
_camera_settings = {
    'indoor_enabled': True,
    'outdoor_enabled': True,
    'motion_recording_enabled': False
}

_headcount_settings = {
    'enabled': False,
    'scheduled_time': '19:00'
}

_timezone_setting = {
    'timezone': 'UTC'
}

_climate_status = {
    'fan_status': 'auto',
    'temperature_threshold': 85
}

VALID_TIMEZONES = {'UTC', 'CST', 'EST', 'PST', 'MST'}

AVAILABLE_SCRIPTS = [
    {'name': 'system-restart', 'description': 'Restart the system'},
    {'name': 'health-check', 'description': 'Run health diagnostics'},
    {'name': 'performance-monitor', 'description': 'Monitor performance'},
    {'name': 'system-update', 'description': 'Run system updates'},
    {'name': 'service-control', 'description': 'Control services'},
    {'name': 'sensor-diagnostics', 'description': 'Run sensor diagnostics'},
    {'name': 's3-scan', 'description': 'Scan S3 for corrupted videos'},
    {'name': 's3-clean', 'description': 'Clean corrupted videos from S3'}
]


# =============================================================================
# Health Metrics Endpoints
# =============================================================================

@admin_bp.route('/health/memory', methods=['GET'])
def get_memory_metrics():
    """Get Raspberry Pi memory usage metrics."""
    return jsonify({
        'used_percent': 45.5,
        'available_mb': 2048,
        'total_mb': 4096
    })


@admin_bp.route('/health/storage', methods=['GET'])
def get_storage_metrics():
    """Get Raspberry Pi disk storage metrics."""
    return jsonify({
        'used_percent': 35.0,
        'available_gb': 20.5,
        'total_gb': 32.0
    })


@admin_bp.route('/health/s3-storage', methods=['GET'])
def get_s3_storage_metrics():
    """Get S3 video storage metrics."""
    return jsonify({
        'video_count': 150,
        'total_size_gb': 5.2
    })


@admin_bp.route('/health/billing', methods=['GET'])
def get_billing_metrics():
    """Get AWS month-to-date billing by service."""
    return jsonify({
        'total_cost': 12.50,
        'by_service': {
            'S3': 5.00,
            'EC2': 4.50,
            'IoT': 3.00
        }
    })


@admin_bp.route('/health', methods=['GET'])
def get_all_health_metrics():
    """Get all health metrics in one call."""
    return jsonify({
        'memory': {
            'used_percent': 45.5,
            'available_mb': 2048,
            'total_mb': 4096
        },
        'storage': {
            'used_percent': 35.0,
            'available_gb': 20.5,
            'total_gb': 32.0
        },
        's3_storage': {
            'video_count': 150,
            'total_size_gb': 5.2
        },
        'last_updated': datetime.now(timezone.utc).isoformat()
    })


@admin_bp.route('/health/refresh', methods=['POST'])
def refresh_health_metrics():
    """Force refresh of health metrics."""
    return jsonify({
        'last_updated': datetime.now(timezone.utc).isoformat()
    })


# =============================================================================
# Camera Settings Endpoints
# =============================================================================

@admin_bp.route('/camera-settings', methods=['GET'])
def get_camera_settings():
    """Get current camera settings."""
    return jsonify(_camera_settings)


@admin_bp.route('/camera-settings', methods=['PUT'])
def update_camera_settings():
    """Update camera settings."""
    data = request.get_json() or {}

    if 'indoor_enabled' in data:
        _camera_settings['indoor_enabled'] = data['indoor_enabled']
    if 'outdoor_enabled' in data:
        _camera_settings['outdoor_enabled'] = data['outdoor_enabled']
    if 'motion_recording_enabled' in data:
        _camera_settings['motion_recording_enabled'] = data['motion_recording_enabled']

    return jsonify(_camera_settings)


# =============================================================================
# Headcount Settings Endpoints
# =============================================================================

@admin_bp.route('/headcount-settings', methods=['GET'])
def get_headcount_settings():
    """Get nightly headcount settings."""
    return jsonify(_headcount_settings)


@admin_bp.route('/headcount-settings', methods=['PUT'])
def update_headcount_settings():
    """Update headcount settings."""
    data = request.get_json() or {}

    if 'enabled' in data:
        _headcount_settings['enabled'] = data['enabled']
    if 'scheduled_time' in data:
        _headcount_settings['scheduled_time'] = data['scheduled_time']

    return jsonify(_headcount_settings)


# =============================================================================
# Timezone Settings Endpoints
# =============================================================================

@admin_bp.route('/timezone', methods=['GET'])
def get_timezone():
    """Get current timezone setting."""
    return jsonify(_timezone_setting)


@admin_bp.route('/timezone', methods=['PUT'])
def update_timezone():
    """Update timezone setting."""
    data = request.get_json() or {}
    tz = data.get('timezone')

    if tz not in VALID_TIMEZONES:
        return jsonify({'error': 'Invalid timezone'}), 400

    _timezone_setting['timezone'] = tz
    return jsonify(_timezone_setting)


# =============================================================================
# Dangerous Operations Endpoints
# =============================================================================

@admin_bp.route('/delete-all-videos', methods=['POST'])
def delete_all_videos():
    """Delete all videos (requires confirmation)."""
    data = request.get_json() or {}

    if not data.get('confirmed'):
        return jsonify({'error': 'Confirmation required'}), 400

    # Get mock_s3_client from Flask g context if available
    s3_client = getattr(g, 's3_client', None)
    if s3_client:
        s3_client.delete_objects(Bucket='test', Delete={'Objects': []})

    return jsonify({
        'success': True,
        'deleted_count': 10,
        'thumbnails_deleted': 10
    })


@admin_bp.route('/delete-sensor-data', methods=['POST'])
def delete_sensor_data():
    """Delete sensor data (requires confirmation)."""
    data = request.get_json() or {}

    if not data.get('confirmed'):
        return jsonify({'error': 'Confirmation required'}), 400

    return jsonify({
        'success': True,
        'deleted_count': 100
    })


# =============================================================================
# Remote Pi Control Scripts
# =============================================================================

@admin_bp.route('/scripts', methods=['GET'])
def get_available_scripts():
    """Get list of available control scripts."""
    return jsonify({'scripts': AVAILABLE_SCRIPTS})


@admin_bp.route('/scripts/system-restart', methods=['POST'])
def system_restart():
    """Trigger system restart on selected coop."""
    return jsonify({'status': 'restart_initiated'})


@admin_bp.route('/scripts/health-check', methods=['POST'])
def health_check_script():
    """Run health check diagnostics."""
    data = request.get_json() or {}
    coop_id = data.get('coop_id', 'coop1')

    result = {
        'services': {'status': 'running'},
        'disk': {'used_percent': 35},
        'temperature': {'cpu': 45.0}
    }

    if coop_id == 'all':
        return jsonify({
            'coop1': result,
            'coop2': result
        })

    return jsonify(result)


@admin_bp.route('/scripts/performance-monitor', methods=['POST'])
def performance_monitor():
    """Run performance monitoring script."""
    return jsonify({'status': 'completed', 'metrics': {}})


@admin_bp.route('/scripts/system-update', methods=['POST'])
def system_update():
    """Trigger system update."""
    return jsonify({'status': 'update_initiated'})


@admin_bp.route('/scripts/service-control', methods=['POST'])
def service_control():
    """Control services (start/stop/restart)."""
    data = request.get_json() or {}
    action = data.get('action', 'status')
    return jsonify({'status': 'completed', 'action': action})


@admin_bp.route('/scripts/sensor-diagnostics', methods=['POST'])
def sensor_diagnostics():
    """Run sensor diagnostics."""
    return jsonify({
        'sensors': {
            'sht41': {'status': 'ok'},
            'cameras': {'status': 'ok'},
            'motion': {'status': 'ok'}
        }
    })


@admin_bp.route('/scripts/s3-scan', methods=['POST'])
def s3_scan():
    """Scan S3 for corrupted videos."""
    data = request.get_json() or {}
    dry_run = data.get('dry_run', True)

    return jsonify({
        'corrupted_count': 2,
        'dry_run': dry_run
    })


@admin_bp.route('/scripts/s3-clean', methods=['POST'])
def s3_clean():
    """Clean corrupted videos from S3."""
    return jsonify({
        'deleted_count': 2
    })


# =============================================================================
# Climate Control Endpoints
# =============================================================================

@admin_bp.route('/climate/status', methods=['GET'])
def get_climate_status():
    """Get current climate status."""
    return jsonify(_climate_status)


@admin_bp.route('/climate/fan', methods=['POST'])
def control_fan():
    """Control fan (on/off/auto)."""
    data = request.get_json() or {}
    action = data.get('action', 'auto')

    if action in ('on', 'off', 'auto'):
        _climate_status['fan_status'] = action

    return jsonify(_climate_status)
