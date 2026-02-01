"""
Chicken Registry API Routes

Endpoints for managing chickens and headcount operations.
"""

from typing import Any, Dict, List, Optional
from flask import Blueprint, request, jsonify

chickens_bp = Blueprint("chickens", __name__)


# =============================================================================
# Database Functions (will be mocked in tests)
# =============================================================================


def get_all_chickens(_active_only: bool = False) -> List[Dict[str, Any]]:
    """Retrieve all chickens from the database.

    Args:
        active_only: If True, return only active chickens.

    Returns:
        List of chicken dictionaries.
    """
    return []


def create_chicken(_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new chicken record in the database.

    Args:
        data: Dictionary containing chicken attributes (name, breed, etc.).

    Returns:
        The created chicken record.
    """
    return _data


def update_chicken(_chicken_id: int, _data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing chicken record.

    Args:
        chicken_id: The unique identifier of the chicken.
        data: Dictionary containing fields to update.

    Returns:
        Updated chicken record, or None if not found.
    """
    return None


def deactivate_chicken(_chicken_id: int) -> bool:
    """Deactivate a chicken (soft delete).

    Args:
        chicken_id: The unique identifier of the chicken.

    Returns:
        True if deactivation was successful.
    """
    return False


def get_latest_headcount() -> Optional[Dict[str, Any]]:
    """Get the most recent headcount result.

    Returns:
        Latest headcount record, or None if no data exists.
    """
    return None


def get_headcount_history(_days: int = 7) -> List[Dict[str, Any]]:
    """Get headcount history for the specified number of days.

    Args:
        days: Number of days of history to retrieve.

    Returns:
        List of headcount records.
    """
    return []


def trigger_headcount() -> Dict[str, Any]:
    """Trigger a manual headcount operation.

    Returns:
        Dictionary with operation status.
    """
    return {"status": "started"}


# =============================================================================
# Blueprint Routes
# =============================================================================


@chickens_bp.route("/api/chickens", methods=["GET"])
def list_chickens():
    """List all chickens in the registry.

    Query Parameters:
        active: Filter to only active chickens ('true'/'false').

    Returns:
        tuple: JSON response with chickens list and expected_count.
    """
    active_only = request.args.get("active", "").lower() == "true"
    chickens = get_all_chickens(active_only)
    active_chickens = [c for c in chickens if c.get("is_active", True)]
    return jsonify({"chickens": chickens, "expected_count": len(active_chickens)}), 200


@chickens_bp.route("/api/chickens", methods=["POST"])
def register_chicken():
    """Register a new chicken in the flock.

    Requires 'name' field in the JSON body.

    Returns:
        tuple: JSON response with created chicken and 201, or error with 400/409.
    """
    data = request.get_json() or {}

    if "name" not in data:
        return jsonify({"error": "Name is required"}), 400

    try:
        chicken = create_chicken(data)
        return jsonify(chicken), 201
    except Exception as e:  # pylint: disable=broad-exception-caught
        return jsonify({"error": str(e)}), 409


@chickens_bp.route("/api/chickens/<int:chicken_id>", methods=["PUT"])
def update_chicken_route(chicken_id):
    """Update an existing chicken's details.

    Args:
        chicken_id: The unique identifier of the chicken to update.

    Returns:
        tuple: JSON response with updated chicken and 200, or error with 404.
    """
    data = request.get_json() or {}
    result = update_chicken(chicken_id, data)  # pylint: disable=assignment-from-none

    if result is None:
        return jsonify({"error": "Chicken not found"}), 404

    return jsonify(result), 200


@chickens_bp.route("/api/chickens/<int:chicken_id>", methods=["DELETE"])
def deactivate_chicken_route(chicken_id):
    """Deactivate a chicken (soft delete).

    Args:
        chicken_id: The unique identifier of the chicken to deactivate.

    Returns:
        tuple: JSON response with success message and 200 status code.
    """
    deactivate_chicken(chicken_id)
    return jsonify({"message": "Chicken deactivated"}), 200


# =============================================================================
# Legacy Route Registration (for backward compatibility)
# =============================================================================


def register_routes(app):
    """Register chicken routes with Flask app (legacy method).

    Args:
        app: The Flask application instance to register the chickens blueprint with.
    """
    if "chickens" not in app.blueprints:
        app.register_blueprint(chickens_bp)
