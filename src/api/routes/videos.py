"""
Video Management API Routes

Endpoints for managing motion-triggered video recordings.
"""

from typing import Any, Dict, List, Optional
from flask import request, jsonify, session


# =============================================================================
# Database Functions (will be mocked in tests)
# =============================================================================

def get_videos(
    camera: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    retained: Optional[str] = None,
    page: Optional[int] = None,
    per_page: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Retrieve videos with optional filtering and pagination.

    Args:
        camera: Filter by camera name (e.g., 'indoor', 'outdoor').
        start_date: Filter videos from this date (ISO format).
        end_date: Filter videos until this date (ISO format).
        retained: Filter by retention status ('true'/'false').
        page: Page number for pagination.
        per_page: Number of results per page.

    Returns:
        List of video dictionaries matching the filter criteria.
    """
    return []


def get_video_by_id(video_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single video by its unique identifier.

    Args:
        video_id: The unique identifier of the video.

    Returns:
        Video dictionary if found, None otherwise.
    """
    return None


def retain_video(s3_key: str, user_id: int, note: Optional[str] = None) -> bool:
    """Mark a video for permanent retention to prevent automatic deletion.

    Args:
        s3_key: The S3 object key identifying the video.
        user_id: The ID of the user requesting retention.
        note: Optional note explaining why video is being retained.

    Returns:
        bool: True if retention was successful, False otherwise.
    """
    return True


def delete_video(video_id: int) -> bool:
    """Delete a video by its unique identifier.

    Args:
        video_id: The unique identifier of the video to delete.

    Returns:
        bool: True if deletion was successful, False if video not found.
    """
    return False


# =============================================================================
# Route Registration
# =============================================================================

def register_routes(app):
    """Register auth-protected video routes with Flask app.

    Overrides any existing video route handlers (e.g., from dashboard blueprint)
    with auth-protected versions that delegate to patchable module functions.

    Args:
        app: The Flask application instance to register routes with.
    """

    def list_videos():
        """List all videos with optional filtering and pagination."""
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401

        camera = request.args.get('camera')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        retained = request.args.get('retained')
        page = request.args.get('page', type=int)
        per_page = request.args.get('per_page', type=int)

        videos = get_videos(
            camera=camera,
            start_date=start_date,
            end_date=end_date,
            retained=retained,
            page=page,
            per_page=per_page
        )

        return jsonify({
            "videos": videos,
            "total": len(videos),
            "page": page or 1
        }), 200

    def retain_video_route():
        """Mark a video for permanent retention."""
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401

        data = request.get_json() or {}

        if 's3_key' not in data:
            return jsonify({"error": "s3_key is required"}), 400

        user_id = session.get('user_id')
        s3_key = data.get('s3_key')
        note = data.get('note')

        retain_video(s3_key=s3_key, user_id=user_id, note=note)

        return jsonify({"message": "Video marked for retention"}), 200

    def delete_video_route(video_id):
        """Delete a video by its ID."""
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401

        try:
            result = delete_video(video_id)

            if not result:
                return jsonify({"error": "Video not found"}), 404

            return jsonify({"message": "Video deleted"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def get_single_video(video_id):
        """Get details for a single video by ID."""
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401

        video = get_video_by_id(video_id)  # pylint: disable=assignment-from-none

        if video is None:
            return jsonify({"error": "Video not found"}), 404

        return jsonify(video), 200

    # Override existing view functions from dashboard blueprint if present
    for endpoint, handler in [
        ('dashboard.get_videos', list_videos),
        ('dashboard.retain_video', retain_video_route),
    ]:
        if endpoint in app.view_functions:
            app.view_functions[endpoint] = handler

    # Register routes that don't exist yet (video detail, delete)
    existing_rules = {rule.rule for rule in app.url_map.iter_rules()}
    if '/api/videos/<int:video_id>' not in existing_rules:
        app.add_url_rule('/api/videos/<int:video_id>', 'get_single_video',
                         get_single_video, methods=['GET'])
        app.add_url_rule('/api/videos/<int:video_id>', 'delete_video_route',
                         delete_video_route, methods=['DELETE'])
