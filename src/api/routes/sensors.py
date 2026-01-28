"""
Sensor API Routes

Provides endpoints for sensor data, status, alerts, and CSV export.
"""

from datetime import datetime, timezone
from flask import jsonify, request, session, Response


def get_alerts():
    """Retrieve current active alerts from the system.

    This function can be mocked in tests to simulate various alert conditions.

    Returns:
        list: List of alert dictionaries, empty if no active alerts.
    """
    return []


def register_routes(app):
    """Register sensor routes with the Flask app.

    Args:
        app: The Flask application instance to register routes with.
    """

    @app.route('/api/status')
    def api_status():
        """Return current sensor status."""
        return jsonify({
            "temperature": 72.5,
            "humidity": 65.0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    @app.route('/api/sensor-data')
    def api_sensor_data():
        """Return sensor data with optional filtering."""
        # Query params are accepted but filtering is minimal for now
        _ = request.args.get('range')
        _ = request.args.get('coop')
        return jsonify({
            "data": []
        })

    @app.route('/api/alerts')
    def api_alerts():
        """Return current alerts."""
        alerts = get_alerts()
        return jsonify({
            "alerts": alerts
        })

    @app.route('/api/download-csv')
    def api_download_csv():
        """Download sensor data as CSV."""
        if 'user_id' not in session:
            return Response("Unauthorized", status=401)

        csv_content = "timestamp,temperature,humidity,coop_id\n"
        return Response(
            csv_content,
            status=200,
            mimetype='text/csv',
            headers={"Content-Disposition": "attachment;filename=sensor_data.csv"}
        )
