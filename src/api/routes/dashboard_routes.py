"""
Dashboard Routes for Chicken Coop API
======================================

Provides endpoints for dashboard functionality including:
- Coop selection and status
- Dashboard refresh controls
- Live camera streaming
- Sensor data charts
- Video grid management
- Data export
"""

from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, Response, g

dashboard_bp = Blueprint('dashboard', __name__)

# Track door check cooldowns (coop_id -> last_check_time)
_door_check_times = {}


# =============================================================================
# Coop Selection Endpoints
# =============================================================================

@dashboard_bp.route('/api/coops', methods=['GET'])
def get_coops():
    """Get list of available coops."""
    return jsonify({
        'coops': [
            {'id': 'coop1', 'name': 'Coop 1'},
            {'id': 'coop2', 'name': 'Coop 2'}
        ]
    })


@dashboard_bp.route('/api/status', methods=['GET'])
def get_status():
    """Get status for coop(s)."""
    coop_id = request.args.get('coop_id')
    now = datetime.now(timezone.utc)

    base_status = {
        'online': True,
        'temperature': 72.5,
        'humidity': 65.0,
        'door_status': 'closed',
        'last_update': now.isoformat(),
        'trend': {
            'temperature': 'stable',
            'humidity': 'stable'
        },
        'alerts': []
    }

    if coop_id == 'all':
        return jsonify({
            'coops': {
                'coop1': {**base_status, 'coop_id': 'coop1'},
                'coop2': {**base_status, 'coop_id': 'coop2'}
            }
        })
    elif coop_id:
        return jsonify({**base_status, 'coop_id': coop_id})

    return jsonify(base_status)


# =============================================================================
# Refresh Control Endpoints
# =============================================================================

@dashboard_bp.route('/api/dashboard/refresh', methods=['POST'])
def refresh_dashboard():
    """Refresh all dashboard data."""
    now = datetime.now(timezone.utc)
    return jsonify({
        'status': {'online': True},
        'sensor_data': {'temperature': 72.5, 'humidity': 65.0},
        'videos': [],
        'last_updated': now.isoformat()
    })


@dashboard_bp.route('/api/settings/auto-refresh', methods=['GET'])
def get_auto_refresh():
    """Get auto-refresh settings."""
    return jsonify({
        'enabled': True,
        'interval_seconds': 30
    })


# =============================================================================
# Door Check Endpoints
# =============================================================================

@dashboard_bp.route('/api/check-door', methods=['POST'])
def check_door():
    """Check door position manually with cooldown."""
    data = request.get_json() or {}
    coop_id = data.get('coop_id', 'coop1')
    now = datetime.now(timezone.utc)

    last_check = _door_check_times.get(coop_id)
    if last_check:
        elapsed = (now - last_check).total_seconds()
        if elapsed < 60:
            return jsonify({
                'door_status': 'closed',
                'cooldown': True,
                'cooldown_remaining': int(60 - elapsed)
            })

    _door_check_times[coop_id] = now
    return jsonify({
        'door_status': 'closed',
        'cooldown': False
    })


# =============================================================================
# Live Camera Endpoints
# =============================================================================

@dashboard_bp.route('/api/camera/live', methods=['GET'])
def get_live_stream():
    """Get live camera stream URL."""
    coop_id = request.args.get('coop_id', 'coop1')
    camera = request.args.get('camera', 'indoor')

    return jsonify({
        'stream_url': f'https://stream.example.com/{coop_id}/{camera}',
        'duration': 30,
        'coop_id': coop_id,
        'camera': camera
    })


# =============================================================================
# Sensor Data Endpoints
# =============================================================================

@dashboard_bp.route('/api/sensor-data', methods=['GET'])
def get_sensor_data():
    """Get sensor data for charts."""
    time_range = request.args.get('range', '24h')
    timezone_param = request.args.get('timezone')

    now = datetime.now(timezone.utc)

    return jsonify({
        'readings': [
            {'timestamp': now.isoformat(), 'temperature': 72.5, 'humidity': 65.0}
        ],
        'range': time_range,
        'timezone': timezone_param or 'UTC',
        'statistics': {
            'temperature': {'min': 68.0, 'max': 78.0, 'avg': 72.5},
            'humidity': {'min': 60.0, 'max': 70.0, 'avg': 65.0}
        }
    })


# =============================================================================
# Video Grid Endpoints
# =============================================================================

@dashboard_bp.route('/api/videos', methods=['GET'])
def get_videos():
    """Get videos with filtering and pagination."""
    camera = request.args.get('camera')
    date_range = request.args.get('date_range')
    sort = request.args.get('sort', 'newest')
    limit = request.args.get('limit', 12, type=int)
    offset = request.args.get('offset', 0, type=int)

    now = datetime.now(timezone.utc)

    # Sample video data
    videos = [
        {
            'id': 'video1',
            'filename': 'motion_20250125_143000.mp4',
            'camera': camera or 'indoor',
            'timestamp': now.isoformat(),
            'file_size': 15000000,
            'trigger_type': 'motion',
            'thumbnail_url': 'https://example.com/thumb1.jpg'
        }
    ]

    # Filter by camera if specified
    if camera:
        videos = [v for v in videos if v['camera'] == camera]

    return jsonify({
        'videos': videos,
        'total': len(videos),
        'limit': limit,
        'offset': offset
    })


@dashboard_bp.route('/api/videos/count', methods=['GET'])
def get_video_count():
    """Get total video count."""
    return jsonify({'total': 42})


@dashboard_bp.route('/api/videos/<video_id>/url', methods=['GET'])
def get_video_url(video_id):
    """Get presigned URL for video playback."""
    s3_client = getattr(g, 's3_client', None)

    if s3_client:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': 'test-bucket', 'Key': f'videos/{video_id}.mp4'},
            ExpiresIn=3600
        )
    else:
        url = f'https://example.com/videos/{video_id}.mp4'

    return jsonify({
        'url': url,
        'expires_in': 3600,
        'video_id': video_id
    })


# =============================================================================
# Manual Recording Endpoint
# =============================================================================

@dashboard_bp.route('/api/manual-record', methods=['POST'])
def manual_record():
    """Trigger manual video recording."""
    data = request.get_json() or {}
    coop_id = data.get('coop_id', 'coop1')
    camera = data.get('camera', 'indoor')

    return jsonify({
        'status': 'recording_started',
        'coop_id': coop_id,
        'camera': camera
    }), 202


# =============================================================================
# Data Export Endpoints
# =============================================================================

@dashboard_bp.route('/api/export/sensor-data', methods=['GET'])
def export_sensor_data():
    """Export sensor data as CSV."""
    format_type = request.args.get('format', 'csv')
    start = request.args.get('start')
    end = request.args.get('end')
    coop_id = request.args.get('coop_id')

    if format_type == 'csv':
        csv_content = "timestamp,temperature,humidity,coop_id\n"
        csv_content += "2025-01-25 14:00:00,72.5,65.0,coop1\n"

        response = Response(
            csv_content,
            status=200,
            headers={"Content-Disposition": "attachment;filename=sensor_data.csv"}
        )
        response.content_type = 'text/csv'
        return response

    return jsonify({'error': 'Unsupported format'}), 400
