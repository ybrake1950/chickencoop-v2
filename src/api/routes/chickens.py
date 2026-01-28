"""
Chicken Registry API Routes

Endpoints for managing chickens and headcount operations.
"""

from typing import Any, Dict, List, Optional
from flask import request, jsonify, session


# =============================================================================
# Database Functions (will be mocked in tests)
# =============================================================================

def get_all_chickens(active_only: bool = False) -> List[Dict[str, Any]]:
    """Retrieve all chickens from database."""
    return []


def create_chicken(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new chicken record."""
    return data


def update_chicken(chicken_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing chicken record. Returns None if not found."""
    return None


def deactivate_chicken(chicken_id: int) -> bool:
    """Deactivate a chicken (soft delete)."""
    return False


def get_latest_headcount() -> Optional[Dict[str, Any]]:
    """Get the most recent headcount result. Returns None if no data."""
    return None


def get_headcount_history(days: int = 7) -> List[Dict[str, Any]]:
    """Get headcount history for specified number of days."""
    return []


def trigger_headcount() -> Dict[str, Any]:
    """Trigger a manual headcount operation."""
    return {"status": "started"}


# =============================================================================
# Route Registration
# =============================================================================

def register_routes(app):
    """Register chicken and headcount routes with Flask app."""

    @app.route('/api/chickens', methods=['GET'])
    def list_chickens():
        """GET /api/chickens - List all chickens."""
        active_only = request.args.get('active', '').lower() == 'true'
        chickens = get_all_chickens(active_only=active_only)
        active_chickens = [c for c in chickens if c.get('is_active', True)]
        return jsonify({
            "chickens": chickens,
            "expected_count": len(active_chickens)
        }), 200

    @app.route('/api/chickens', methods=['POST'])
    def register_chicken():
        """POST /api/chickens - Register a new chicken."""
        data = request.get_json() or {}

        if 'name' not in data:
            return jsonify({"error": "Name is required"}), 400

        try:
            chicken = create_chicken(data)
            return jsonify(chicken), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 409

    @app.route('/api/chickens/<int:chicken_id>', methods=['PUT'])
    def update_chicken_route(chicken_id):
        """PUT /api/chickens/<id> - Update chicken details."""
        data = request.get_json() or {}
        result = update_chicken(chicken_id, data)  # pylint: disable=assignment-from-none

        if result is None:
            return jsonify({"error": "Chicken not found"}), 404

        return jsonify(result), 200

    @app.route('/api/chickens/<int:chicken_id>', methods=['DELETE'])
    def deactivate_chicken_route(chicken_id):
        """DELETE /api/chickens/<id> - Deactivate chicken."""
        deactivate_chicken(chicken_id)
        return jsonify({"message": "Chicken deactivated"}), 200

    @app.route('/api/headcount/latest', methods=['GET'])
    def get_latest_headcount_route():
        """GET /api/headcount/latest - Get latest headcount."""
        result = get_latest_headcount()  # pylint: disable=assignment-from-none

        if result is None:
            return jsonify({"message": "No headcount data"}), 204

        return jsonify(result), 200

    @app.route('/api/headcount/history', methods=['GET'])
    def get_headcount_history_route():
        """GET /api/headcount/history - Get headcount history."""
        days = request.args.get('days', 7, type=int)
        history = get_headcount_history(days=days)
        return jsonify(history), 200

    @app.route('/api/headcount/run', methods=['POST'])
    def run_headcount():
        """POST /api/headcount/run - Trigger manual headcount."""
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401

        result = trigger_headcount()
        return jsonify(result), 202
