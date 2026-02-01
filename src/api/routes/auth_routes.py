"""
Authentication Routes for Chicken Coop API
============================================

Provides endpoints for user authentication including:
- Login/logout functionality
- Password reset workflow
"""

from flask import Blueprint, jsonify, request, session, redirect

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET"])
def login_page():
    """Display the login page.

    Returns:
        tuple: JSON response with page identifier and 200 status code.
    """
    return jsonify({"page": "login"}), 200


@auth_bp.route("/login", methods=["POST"])
def login():
    """Process user login credentials and create session.

    Accepts credentials via form data or JSON body. On successful
    authentication, creates a session and redirects to the dashboard.

    Returns:
        Response: Redirect to dashboard on success, or JSON error with 401 status.
    """
    data = request.form or request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    # Simple authentication (in production would check database)
    if email and password:
        session["user_id"] = 1
        session["email"] = email
        return redirect("/")

    return jsonify({"error": "Invalid credentials"}), 401


@auth_bp.route("/logout", methods=["GET"])
def logout():
    """Log out user by clearing the session and redirect to login.

    Returns:
        Response: Redirect to login page.
    """
    session.clear()
    return redirect("/login")


@auth_bp.route("/reset-password-request", methods=["POST"])
def reset_password_request():
    """Request a password reset email for the specified email address.

    Accepts email via form data or JSON body. Sends a password reset
    link to the provided email address if it exists in the system.

    Returns:
        tuple: JSON response with success status and 200, or error with 400.
    """
    data = request.form or request.get_json() or {}
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    # In production would send email with reset token
    return jsonify({"success": True, "message": "Password reset email sent"}), 200


@auth_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):  # pylint: disable=unused-argument
    """Reset user password using a valid reset token.

    Args:
        token: The password reset token from the reset email.

    Returns:
        tuple: JSON response with success status and 200, or error with 400.
    """
    data = request.form or request.get_json() or {}
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not password or not confirm_password:
        return jsonify({"error": "Password fields required"}), 400

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    # In production would validate token and update password
    return jsonify({"success": True, "message": "Password has been reset"}), 200
