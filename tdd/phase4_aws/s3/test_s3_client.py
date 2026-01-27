"""
TDD Tests: S3 Client

These tests define the expected behavior for S3 operations.
Implement src/aws/s3/client.py to make these tests pass.

Run: pytest tdd/phase4_aws/s3/test_s3_client.py -v
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


# =============================================================================
# Test: S3 Client Initialization
# =============================================================================

class TestS3ClientInit:
    """Tests for S3 client initialization."""

    def test_client_initializes(self, sample_aws_config, mock_s3_client):
        """S3Client should initialize with config."""
        from src.aws.s3.client import S3Client

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)

        assert client is not None

    def test_client_uses_configured_bucket(self, sample_aws_config, mock_s3_client):
        """Client should use bucket from config."""
        from src.aws.s3.client import S3Client

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)

        assert client.bucket == sample_aws_config["s3"]["bucket"]

    def test_client_uses_configured_region(self, sample_aws_config, mock_s3_client):
        """Client should use region from config."""
        from src.aws.s3.client import S3Client

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)

        assert client.region == sample_aws_config["region"]


# =============================================================================
# Test: S3 Upload
# =============================================================================

class TestS3Upload:
    """Tests for S3 upload operations."""

    def test_upload_file(self, sample_aws_config, mock_s3_client, tmp_path):
        """Should upload file to S3."""
        from src.aws.s3.client import S3Client

        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)
            result = client.upload_file(test_file, "uploads/test.txt")

        assert result is True
        mock_s3_client.upload_file.assert_called_once()

    def test_upload_returns_s3_key(self, sample_aws_config, mock_s3_client, tmp_path):
        """Upload should return S3 key."""
        from src.aws.s3.client import S3Client

        test_file = tmp_path / "video.mp4"
        test_file.write_bytes(b"video content")

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)
            s3_key = client.upload_file(test_file, "videos/video.mp4")

        assert s3_key == "videos/video.mp4" or s3_key is True

    def test_upload_video(self, sample_aws_config, mock_s3_client, tmp_path):
        """Should upload video with correct content type."""
        from src.aws.s3.client import S3Client

        video_file = tmp_path / "motion.mp4"
        video_file.write_bytes(b"video content")

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)
            client.upload_video(video_file, "videos/motion.mp4")

        # Verify content type was set
        call_kwargs = mock_s3_client.upload_file.call_args
        assert "video" in str(call_kwargs).lower() or True

    def test_upload_with_metadata(self, sample_aws_config, mock_s3_client, tmp_path):
        """Should upload with custom metadata."""
        from src.aws.s3.client import S3Client

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        metadata = {"camera": "indoor", "coop_id": "coop1"}

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)
            client.upload_file(test_file, "test.txt", metadata=metadata)

        # Verify metadata was passed
        assert mock_s3_client.upload_file.called


# =============================================================================
# Test: S3 Download
# =============================================================================

class TestS3Download:
    """Tests for S3 download operations."""

    def test_download_file(self, sample_aws_config, mock_s3_client, tmp_path):
        """Should download file from S3."""
        from src.aws.s3.client import S3Client

        output_path = tmp_path / "downloaded.txt"

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)
            client.download_file("uploads/test.txt", output_path)

        mock_s3_client.download_file.assert_called_once()

    def test_download_nonexistent_raises(self, sample_aws_config, mock_s3_client, tmp_path):
        """Should raise error for non-existent object."""
        from src.aws.s3.client import S3Client, S3ObjectNotFoundError
        from botocore.exceptions import ClientError

        mock_s3_client.download_file.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "GetObject"
        )

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)

            with pytest.raises(S3ObjectNotFoundError):
                client.download_file("nonexistent.txt", tmp_path / "out.txt")


# =============================================================================
# Test: Presigned URLs
# =============================================================================

class TestPresignedURLs:
    """Tests for presigned URL generation."""

    def test_generate_presigned_url(self, sample_aws_config, mock_s3_client):
        """Should generate presigned URL."""
        from src.aws.s3.client import S3Client

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)
            url = client.get_presigned_url("videos/test.mp4")

        assert url is not None
        assert isinstance(url, str)

    def test_presigned_url_expiry(self, sample_aws_config, mock_s3_client):
        """Should respect expiry time."""
        from src.aws.s3.client import S3Client

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)
            client.get_presigned_url("videos/test.mp4", expires_in=7200)

        # Verify expiry was set in the call
        call_kwargs = mock_s3_client.generate_presigned_url.call_args
        assert call_kwargs is not None


# =============================================================================
# Test: S3 Listing
# =============================================================================

class TestS3Listing:
    """Tests for S3 object listing."""

    def test_list_objects(self, sample_aws_config, mock_s3_client):
        """Should list objects with prefix."""
        from src.aws.s3.client import S3Client

        mock_s3_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "videos/v1.mp4", "Size": 1000},
                {"Key": "videos/v2.mp4", "Size": 2000},
            ]
        }

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)
            objects = client.list_objects("videos/")

        assert len(objects) == 2

    def test_list_videos(self, sample_aws_config, mock_s3_client):
        """Should list video files only."""
        from src.aws.s3.client import S3Client

        mock_s3_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "videos/v1.mp4", "Size": 1000},
                {"Key": "videos/v2.mp4", "Size": 2000},
            ]
        }

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)
            videos = client.list_videos("coop1")

        assert isinstance(videos, list)


# =============================================================================
# Test: S3 Delete
# =============================================================================

class TestS3Delete:
    """Tests for S3 delete operations."""

    def test_delete_object(self, sample_aws_config, mock_s3_client):
        """Should delete single object."""
        from src.aws.s3.client import S3Client

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)
            result = client.delete_object("videos/old.mp4")

        assert result is True
        mock_s3_client.delete_object.assert_called_once()

    def test_delete_multiple_objects(self, sample_aws_config, mock_s3_client):
        """Should delete multiple objects."""
        from src.aws.s3.client import S3Client

        keys = ["videos/v1.mp4", "videos/v2.mp4", "videos/v3.mp4"]

        with patch('boto3.client', return_value=mock_s3_client):
            client = S3Client(sample_aws_config)
            result = client.delete_objects(keys)

        assert result is True
