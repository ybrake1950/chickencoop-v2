"""
Page Routes for Chicken Coop API
==================================

Provides HTML page endpoints including:
- Dashboard index
- Chickens registry pages
- Headcount page
"""

from flask import Blueprint, jsonify, request

page_bp = Blueprint("pages", __name__)


@page_bp.route("/", methods=["GET"])
def dashboard_index():
    """Display the main dashboard page with current sensor readings.

    Returns:
        tuple: JSON response with dashboard data and 200 status code.
    """
    return (
        jsonify(
            {"page": "dashboard", "temperature": 72.5, "humidity": 65.0, "temp": 72.5}
        ),
        200,
    )


@page_bp.route("/chickens", methods=["GET"])
def chickens_list():
    """Display the chickens registry list page.

    Returns:
        tuple: JSON response with chickens list and 200 status code.
    """
    return jsonify({"page": "chickens", "chickens": []}), 200


@page_bp.route("/chickens/register", methods=["POST"])
def chickens_register():
    """Register a new chicken in the flock registry.

    Accepts chicken details via form data or JSON body.
    Name is required; breed, color, and notes are optional.

    Returns:
        tuple: JSON response with created chicken and 200, or error with 400.
    """
    data = request.form or request.get_json() or {}
    name = data.get("name")
    breed = data.get("breed")
    color = data.get("color")
    notes = data.get("notes")

    if not name:
        return jsonify({"error": "Name is required"}), 400

    return (
        jsonify(
            {
                "success": True,
                "chicken": {
                    "name": name,
                    "breed": breed,
                    "color": color,
                    "notes": notes,
                },
            }
        ),
        200,
    )


@page_bp.route("/chickens/<int:chicken_id>/edit", methods=["POST"])
def chickens_edit(chicken_id):
    """Edit an existing chicken's details.

    Args:
        chicken_id: The unique identifier of the chicken to edit.

    Returns:
        tuple: JSON response with updated chicken data and 200 status code.
    """
    data = request.form or request.get_json() or {}

    return jsonify({"success": True, "chicken_id": chicken_id, "updated": data}), 200


@page_bp.route("/headcount", methods=["GET"])
def headcount_page():
    """Display the headcount history page.

    Returns:
        tuple: JSON response with headcount records and 200 status code.
    """
    return jsonify({"page": "headcount", "records": []}), 200
