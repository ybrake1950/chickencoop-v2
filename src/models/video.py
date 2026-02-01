"""
Video Metadata Models

Models for managing video metadata, retention policies, and collections.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any


class ValidationError(Exception):
    """Raised when validation fails."""


class VideoMetadata:
    """Model for video metadata with retention and file information."""

    def __init__(
        self,
        filename: str,
        s3_key: str,
        camera: str,
        upload_date: Optional[datetime] = None,
        size_bytes: Optional[int] = None,
        duration: Optional[int] = None,
        retain_permanently: bool = False,
        retained_by_user_id: Optional[int] = None,
        retention_note: Optional[str] = None,
        retained_at: Optional[datetime] = None,
    ):
        """Initialize video metadata.

        Args:
            filename: Original video filename.
            s3_key: S3 object key for the video.
            camera: Camera type ('indoor' or 'outdoor').
            upload_date: When the video was uploaded (defaults to now UTC).
            size_bytes: File size in bytes.
            duration: Video duration in seconds.
            retain_permanently: Whether video is marked for permanent retention.
            retained_by_user_id: ID of user who marked retention.
            retention_note: Note explaining why video is retained.
            retained_at: When retention was marked.
        """
        self.filename = filename
        self.s3_key = s3_key
        self.camera = camera
        self.upload_date = upload_date or datetime.now(timezone.utc)
        self.size_bytes = size_bytes
        self.duration = duration
        self.retain_permanently = retain_permanently
        self.retained_by_user_id = retained_by_user_id
        self.retention_note = retention_note
        self.retained_at = retained_at
        self.has_thumbnail = False

    def validate(self):
        """Validate the video metadata."""
        if self.camera not in ["indoor", "outdoor"]:
            raise ValidationError(
                f"Camera must be 'indoor' or 'outdoor', got '{self.camera}'"
            )

    def mark_for_retention(self, user_id: int, note: str = ""):
        """Mark video for permanent retention."""
        self.retain_permanently = True
        self.retained_by_user_id = user_id
        self.retention_note = note
        self.retained_at = datetime.now(timezone.utc)

    def remove_retention(self):
        """Remove retention status from video."""
        self.retain_permanently = False
        self.retained_by_user_id = None
        self.retention_note = None
        self.retained_at = None

    def is_expired(self) -> bool:
        """Check if video has expired (120 days for non-retained)."""
        if self.retain_permanently:
            return False

        expiration_days = 120
        expiration_date = datetime.now(timezone.utc) - timedelta(days=expiration_days)
        return self.upload_date < expiration_date

    @property
    def size_formatted(self) -> str:
        """Return formatted file size."""
        if self.size_bytes is None:
            return "Unknown"

        # Convert to appropriate unit
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        elif self.size_bytes < 1024 * 1024 * 1024:
            return f"{self.size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{self.size_bytes / (1024 * 1024 * 1024):.1f} GB"

    @property
    def duration_formatted(self) -> str:
        """Return formatted duration."""
        if self.duration is None:
            return "Unknown"

        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"

    @property
    def thumbnail_key(self) -> str:
        """Generate thumbnail S3 key from video key."""
        # Replace video extension with .jpg and add thumbnail prefix/suffix
        base_key = self.s3_key.rsplit(".", 1)[0]
        return f"{base_key}_thumbnail.jpg"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "filename": self.filename,
            "s3_key": self.s3_key,
            "camera": self.camera,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "size_bytes": self.size_bytes,
            "duration": self.duration,
            "retain_permanently": self.retain_permanently,
            "retained_by_user_id": self.retained_by_user_id,
            "retention_note": self.retention_note,
            "retained_at": self.retained_at.isoformat() if self.retained_at else None,
            "has_thumbnail": self.has_thumbnail,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VideoMetadata":
        """Create instance from dictionary."""
        # Convert ISO format strings back to datetime
        upload_date = data.get("upload_date")
        if isinstance(upload_date, str):
            upload_date = datetime.fromisoformat(upload_date)

        retained_at = data.get("retained_at")
        if isinstance(retained_at, str):
            retained_at = datetime.fromisoformat(retained_at)

        return cls(
            filename=data["filename"],
            s3_key=data["s3_key"],
            camera=data["camera"],
            upload_date=upload_date,
            size_bytes=data.get("size_bytes"),
            duration=data.get("duration"),
            retain_permanently=data.get("retain_permanently", False),
            retained_by_user_id=data.get("retained_by_user_id"),
            retention_note=data.get("retention_note"),
            retained_at=retained_at,
        )

    def to_api_response(self) -> Dict[str, Any]:
        """Format for API response."""
        return {
            "filename": self.filename,
            "s3_key": self.s3_key,
            "url": self.s3_key,
            "camera": self.camera,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "size": self.size_formatted,
            "size_bytes": self.size_bytes,
            "duration": self.duration_formatted if self.duration else None,
            "duration_seconds": self.duration,
            "thumbnail": self.thumbnail_key,
            "thumbnail_url": self.thumbnail_key,
            "retained": self.retain_permanently,
        }


class VideoList:
    """Collection of VideoMetadata objects with filtering and sorting."""

    def __init__(self, videos: Optional[List[VideoMetadata]] = None):
        """Initialize video list collection.

        Args:
            videos: Optional list of VideoMetadata objects.
        """
        self._videos = videos or []

    def __len__(self) -> int:
        """Return number of videos in collection."""
        return len(self._videos)

    def __getitem__(self, index: int) -> VideoMetadata:
        """Get video by index."""
        return self._videos[index]

    def filter_by_camera(self, camera: str) -> "VideoList":
        """Filter videos by camera type."""
        filtered = [v for v in self._videos if v.camera == camera]
        return VideoList(filtered)

    def filter_retained(self) -> "VideoList":
        """Filter to only retained videos."""
        filtered = [v for v in self._videos if v.retain_permanently]
        return VideoList(filtered)

    @property
    def total_size_bytes(self) -> int:
        """Calculate total size of all videos."""
        return sum(v.size_bytes or 0 for v in self._videos)

    def sort_by_date(self, ascending: bool = True) -> "VideoList":
        """Sort videos by upload date."""
        sorted_videos = sorted(
            self._videos, key=lambda v: v.upload_date, reverse=not ascending
        )
        return VideoList(sorted_videos)
