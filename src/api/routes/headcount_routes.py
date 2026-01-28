"""
Headcount Routes for Chicken Coop API
======================================

Provides endpoints for headcount operations including:
- Latest headcount result
- Headcount statistics
- Historical headcount records
- Manual headcount trigger
- Chart data for visualizations
- Warning messages
"""

import uuid
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request

headcount_bp = Blueprint('headcount', __name__, url_prefix='/api/headcount')

# In-memory state for headcount (in production would use database)
_headcount_running = False

# Sample headcount data for testing
_sample_records = [
    {
        'timestamp': '2025-01-27T19:00:00+00:00',
        'detected_count': 6,
        'expected_count': 6,
        'all_present': True,
        'confidence': 95,
        'method': 'automated',
        'missing_count': 0,
        'notes': None
    },
    {
        'timestamp': '2025-01-26T19:00:00+00:00',
        'detected_count': 5,
        'expected_count': 6,
        'all_present': False,
        'confidence': 88,
        'method': 'simple_count',
        'missing_count': 1,
        'notes': 'One chicken found outside'
    },
    {
        'timestamp': '2025-01-25T19:00:00+00:00',
        'detected_count': 6,
        'expected_count': 6,
        'all_present': True,
        'confidence': 92,
        'method': 'ml_detect',
        'missing_count': 0,
        'notes': None
    },
]


@headcount_bp.route('/latest', methods=['GET'])
def get_latest_headcount():
    """Get the most recent headcount result.

    Returns:
        tuple: JSON response with latest headcount data and 200,
               or error with 404 if no data exists.
    """
    if not _sample_records:
        return jsonify({'error': 'No headcount data'}), 404

    latest = _sample_records[0]
    return jsonify({
        'detected_count': latest['detected_count'],
        'count_detected': latest['detected_count'],
        'count': latest['detected_count'],
        'expected_count': latest['expected_count'],
        'timestamp': latest['timestamp'],
        'confidence': latest['confidence'],
        'method': latest['method'],
        'all_present': latest['all_present']
    })


@headcount_bp.route('/stats', methods=['GET'])
def get_headcount_stats():
    """Get overall headcount statistics including success rate and streaks.

    Returns:
        tuple: JSON response with success_rate, total_checks, and current_streak.
    """
    total_checks = len(_sample_records)
    successful_checks = sum(1 for r in _sample_records if r['all_present'])
    success_rate = (successful_checks / total_checks * 100) if total_checks > 0 else 0

    # Calculate current streak
    current_streak = 0
    for record in _sample_records:
        if record['all_present']:
            current_streak += 1
        else:
            break

    return jsonify({
        'success_rate': success_rate,
        'total_checks': total_checks,
        'current_streak': current_streak
    })


@headcount_bp.route('/history', methods=['GET'])
def get_headcount_history():
    """Get historical headcount records with optional limit.

    Query Parameters:
        limit: Maximum number of records to return (default: 30).

    Returns:
        tuple: JSON response with list of headcount records.
    """
    limit = request.args.get('limit', 30, type=int)
    records = _sample_records[:limit]
    return jsonify({'records': records})


@headcount_bp.route('/run', methods=['POST'])
def trigger_manual_headcount():
    """Trigger a manual headcount check for a specific coop.

    Initiates an asynchronous headcount operation. Returns 409 if
    a headcount is already in progress.

    Returns:
        tuple: JSON response with job_id and 202 on success,
               or 409 if headcount already running.
    """
    global _headcount_running

    data = request.get_json(silent=True) or {}
    coop_id = data.get('coop_id', 'default')

    if _headcount_running:
        return jsonify({
            'status': 'queued',
            'message': 'Headcount already in progress, request queued'
        }), 409

    _headcount_running = True
    job_id = str(uuid.uuid4())

    # Simulate async operation - in real implementation would queue job
    _headcount_running = False

    return jsonify({
        'status': 'started',
        'job_id': job_id,
        'message': f'Headcount started for {coop_id}',
        'estimated_time': 30
    }), 202


@headcount_bp.route('/chart', methods=['GET'])
def get_chart_data():
    """Get formatted data for headcount trend chart visualization.

    Query Parameters:
        days: Number of days of data to return (default: 30).

    Returns:
        tuple: JSON response with data_points array for charting.
    """
    days = request.args.get('days', 30, type=int)

    data_points = [
        {
            'timestamp': record['timestamp'],
            'date': record['timestamp'][:10],
            'detected': record['detected_count'],
            'count': record['detected_count'],
            'expected': record['expected_count']
        }
        for record in _sample_records[:days]
    ]

    return jsonify({'data_points': data_points})


@headcount_bp.route('/warnings', methods=['GET'])
def get_headcount_warnings():
    """Get active warning messages related to headcount.

    Returns warnings if no chickens are registered or no headcount data exists.

    Returns:
        tuple: JSON response with warnings list and chicken_count.
    """
    warnings = []
    chicken_count = 6  # Would come from database

    if chicken_count == 0:
        warnings.append('No chickens registered. Please register your flock.')

    if not _sample_records:
        warnings.append('No headcount data available.')

    return jsonify({
        'warnings': warnings,
        'chicken_count': chicken_count
    })
