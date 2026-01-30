"""Video repository for database operations."""

from typing import Any, Dict, List, Optional


class VideoRepository:
    """Repository for video database operations."""

    def __init__(self, database=None):
        """Initialize video repository with database connection.

        Args:
            database: Database instance for video operations.
        """
        self._db = database

    def find_by_id(self, video_id: int) -> Optional[Dict[str, Any]]:
        """Find a video by ID.

        Args:
            video_id: The video record ID to look up.

        Returns:
            Video metadata dictionary, or None if not found.
        """
        cursor = self._db.connection.cursor()
        cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def find_by_coop(self, coop_id: str) -> List[Dict[str, Any]]:
        """Find videos by coop ID.

        Args:
            coop_id: Coop identifier to filter by (matched against camera field).

        Returns:
            List of video metadata dictionaries.
        """
        cursor = self._db.connection.cursor()
        cursor.execute("SELECT * FROM videos WHERE camera = ?", (coop_id,))
        return [dict(row) for row in cursor.fetchall()]

    def save(self, video_data: Dict[str, Any]) -> int:
        """Save video metadata to the database.

        Args:
            video_data: Dictionary with keys: filename, s3_key, camera,
                duration, size_bytes, upload_date.

        Returns:
            The new video record's ID.
        """
        cursor = self._db.connection.cursor()
        cursor.execute(
            """INSERT INTO videos (filename, s3_key, camera, duration, size_bytes, upload_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                video_data.get("filename"),
                video_data.get("s3_key"),
                video_data.get("camera"),
                video_data.get("duration"),
                video_data.get("size_bytes"),
                video_data.get("upload_date"),
            )
        )
        self._db.connection.commit()
        return cursor.lastrowid
