"""
TDD Tests: Video Metadata Models

These tests define the expected behavior for video metadata models.
Implement src/models/video.py to make these tests pass.

Run: pytest tdd/phase1_foundation/models/test_video_models.py -v
"""

import pytest
from datetime import datetime, timezone, timedelta


# =============================================================================
# Test: VideoMetadata Model
# =============================================================================

class TestVideoMetadataModel:
    """Tests for the VideoMetadata model."""

    def test_video_requires_filename(self):
        """VideoMetadata must have filename."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="motion_20250125_143000.mp4",
            s3_key="videos/coop1/motion_20250125_143000.mp4",
            camera="indoor"
        )

        assert video.filename == "motion_20250125_143000.mp4"

    def test_video_requires_s3_key(self):
        """VideoMetadata must have s3_key."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="motion_20250125_143000.mp4",
            s3_key="videos/coop1/motion_20250125_143000.mp4",
            camera="indoor"
        )

        assert video.s3_key == "videos/coop1/motion_20250125_143000.mp4"

    def test_video_requires_camera(self):
        """VideoMetadata must have camera identifier."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="motion_20250125_143000.mp4",
            s3_key="videos/coop1/motion_20250125_143000.mp4",
            camera="outdoor"
        )

        assert video.camera == "outdoor"

    def test_video_camera_must_be_valid(self):
        """Camera must be 'indoor' or 'outdoor'."""
        from src.models.video import VideoMetadata, ValidationError

        with pytest.raises(ValidationError):
            video = VideoMetadata(
                filename="test.mp4",
                s3_key="videos/test.mp4",
                camera="invalid_camera"
            )
            video.validate()

    def test_video_has_upload_date(self):
        """VideoMetadata should have upload_date."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="test.mp4",
            s3_key="videos/test.mp4",
            camera="indoor"
        )

        assert hasattr(video, 'upload_date')
        assert isinstance(video.upload_date, datetime)


# =============================================================================
# Test: Video Retention
# =============================================================================

class TestVideoRetention:
    """Tests for video retention functionality."""

    def test_video_default_not_retained(self):
        """Videos should not be retained by default."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="test.mp4",
            s3_key="videos/test.mp4",
            camera="indoor"
        )

        assert video.retain_permanently is False

    def test_mark_for_retention(self):
        """Should be able to mark video for retention."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="test.mp4",
            s3_key="videos/test.mp4",
            camera="indoor"
        )

        video.mark_for_retention(user_id=1, note="Special event")

        assert video.retain_permanently is True
        assert video.retained_by_user_id == 1
        assert video.retention_note == "Special event"
        assert video.retained_at is not None

    def test_remove_retention(self):
        """Should be able to remove retention status."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="test.mp4",
            s3_key="videos/test.mp4",
            camera="indoor",
            retain_permanently=True
        )

        video.remove_retention()

        assert video.retain_permanently is False

    def test_is_expired_without_retention(self):
        """Non-retained videos should expire after 120 days."""
        from src.models.video import VideoMetadata

        old_date = datetime.now(timezone.utc) - timedelta(days=121)
        video = VideoMetadata(
            filename="test.mp4",
            s3_key="videos/test.mp4",
            camera="indoor",
            upload_date=old_date
        )

        assert video.is_expired() is True

    def test_not_expired_when_retained(self):
        """Retained videos should never expire."""
        from src.models.video import VideoMetadata

        old_date = datetime.now(timezone.utc) - timedelta(days=500)
        video = VideoMetadata(
            filename="test.mp4",
            s3_key="videos/test.mp4",
            camera="indoor",
            upload_date=old_date,
            retain_permanently=True
        )

        assert video.is_expired() is False


# =============================================================================
# Test: Video File Attributes
# =============================================================================

class TestVideoFileAttributes:
    """Tests for video file attribute handling."""

    def test_video_size_bytes(self):
        """Should store size in bytes."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="test.mp4",
            s3_key="videos/test.mp4",
            camera="indoor",
            size_bytes=15000000
        )

        assert video.size_bytes == 15000000

    def test_video_size_formatted(self):
        """Should format size for display."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="test.mp4",
            s3_key="videos/test.mp4",
            camera="indoor",
            size_bytes=15000000
        )

        # Should return something like "14.3 MB"
        formatted = video.size_formatted
        assert "MB" in formatted or "GB" in formatted

    def test_video_duration_seconds(self):
        """Should store duration in seconds."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="test.mp4",
            s3_key="videos/test.mp4",
            camera="indoor",
            duration=30
        )

        assert video.duration == 30

    def test_video_duration_formatted(self):
        """Should format duration for display."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="test.mp4",
            s3_key="videos/test.mp4",
            camera="indoor",
            duration=90
        )

        # Should return "1:30" or similar
        formatted = video.duration_formatted
        assert ":" in formatted


# =============================================================================
# Test: Video Serialization
# =============================================================================

class TestVideoSerialization:
    """Tests for VideoMetadata serialization."""

    def test_to_dict_includes_all_fields(self):
        """to_dict should include all fields."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="test.mp4",
            s3_key="videos/test.mp4",
            camera="indoor",
            size_bytes=15000000
        )

        result = video.to_dict()

        assert "filename" in result
        assert "s3_key" in result
        assert "camera" in result
        assert "upload_date" in result
        assert "retain_permanently" in result

    def test_from_dict_creates_instance(self):
        """from_dict should create VideoMetadata."""
        from src.models.video import VideoMetadata

        data = {
            "filename": "test.mp4",
            "s3_key": "videos/test.mp4",
            "camera": "indoor",
            "upload_date": datetime.now(timezone.utc).isoformat(),
            "size_bytes": 15000000
        }

        video = VideoMetadata.from_dict(data)

        assert video.filename == "test.mp4"
        assert video.size_bytes == 15000000

    def test_to_api_response_format(self):
        """Should format for API response."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="test.mp4",
            s3_key="videos/test.mp4",
            camera="indoor",
            size_bytes=15000000
        )

        result = video.to_api_response()

        assert "url" in result or "presigned_url" in result or "s3_key" in result
        assert "thumbnail" in result or "thumbnail_url" in result or "s3_key" in result


# =============================================================================
# Test: Video Thumbnail
# =============================================================================

class TestVideoThumbnail:
    """Tests for video thumbnail handling."""

    def test_get_thumbnail_key(self):
        """Should generate thumbnail S3 key from video key."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="motion_20250125.mp4",
            s3_key="videos/coop1/motion_20250125.mp4",
            camera="indoor"
        )

        thumbnail_key = video.thumbnail_key

        assert "thumbnail" in thumbnail_key.lower()
        assert thumbnail_key.endswith(".jpg") or thumbnail_key.endswith(".png")

    def test_has_thumbnail_property(self):
        """Should indicate if thumbnail exists."""
        from src.models.video import VideoMetadata

        video = VideoMetadata(
            filename="test.mp4",
            s3_key="videos/test.mp4",
            camera="indoor"
        )

        # By default, no thumbnail
        assert hasattr(video, 'has_thumbnail')


# =============================================================================
# Test: VideoList Collection
# =============================================================================

class TestVideoList:
    """Tests for video list operations."""

    def test_video_list_can_hold_multiple(self):
        """VideoList should hold multiple videos."""
        from src.models.video import VideoMetadata, VideoList

        videos = VideoList([
            VideoMetadata(filename="v1.mp4", s3_key="v1", camera="indoor"),
            VideoMetadata(filename="v2.mp4", s3_key="v2", camera="outdoor"),
        ])

        assert len(videos) == 2

    def test_filter_by_camera(self):
        """Should filter videos by camera."""
        from src.models.video import VideoMetadata, VideoList

        videos = VideoList([
            VideoMetadata(filename="v1.mp4", s3_key="v1", camera="indoor"),
            VideoMetadata(filename="v2.mp4", s3_key="v2", camera="outdoor"),
            VideoMetadata(filename="v3.mp4", s3_key="v3", camera="indoor"),
        ])

        indoor = videos.filter_by_camera("indoor")

        assert len(indoor) == 2

    def test_filter_retained(self):
        """Should filter retained videos."""
        from src.models.video import VideoMetadata, VideoList

        videos = VideoList([
            VideoMetadata(filename="v1.mp4", s3_key="v1", camera="indoor", retain_permanently=True),
            VideoMetadata(filename="v2.mp4", s3_key="v2", camera="outdoor"),
        ])

        retained = videos.filter_retained()

        assert len(retained) == 1

    def test_total_size_bytes(self):
        """Should calculate total size."""
        from src.models.video import VideoMetadata, VideoList

        videos = VideoList([
            VideoMetadata(filename="v1.mp4", s3_key="v1", camera="indoor", size_bytes=1000),
            VideoMetadata(filename="v2.mp4", s3_key="v2", camera="outdoor", size_bytes=2000),
        ])

        assert videos.total_size_bytes == 3000

    def test_sort_by_date(self):
        """Should sort videos by date."""
        from src.models.video import VideoMetadata, VideoList

        older = datetime.now(timezone.utc) - timedelta(days=1)
        newer = datetime.now(timezone.utc)

        videos = VideoList([
            VideoMetadata(filename="old.mp4", s3_key="old", camera="indoor", upload_date=older),
            VideoMetadata(filename="new.mp4", s3_key="new", camera="indoor", upload_date=newer),
        ])

        sorted_desc = videos.sort_by_date(ascending=False)

        assert sorted_desc[0].filename == "new.mp4"
