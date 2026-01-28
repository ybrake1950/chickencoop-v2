"""S3 Client for ChickenCoop AWS operations."""
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError


class S3ObjectNotFoundError(Exception):
    """Raised when an S3 object is not found."""
    pass


class S3Client:
    """
    Client for AWS S3 storage operations.

    Handles file uploads, downloads, presigned URL generation, and object management
    for the ChickenCoop application.

    Attributes:
        region: AWS region for S3 operations.
        bucket: S3 bucket name for storage.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize S3 client with AWS configuration.

        Args:
            config: AWS configuration dictionary containing region and s3 settings.
        """
        self.region = config["region"]
        self.bucket = config["s3"]["bucket"]
        self._client = boto3.client("s3", region_name=self.region)

    def upload_file(
        self,
        local_path: Path,
        s3_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Upload a file to S3.

        Args:
            local_path: Path to the local file to upload.
            s3_key: Destination key (path) in S3 bucket.
            metadata: Optional metadata dictionary to attach to the object.

        Returns:
            True if upload succeeded.
        """
        extra_args = {}
        if metadata:
            extra_args["Metadata"] = metadata

        self._client.upload_file(
            str(local_path),
            self.bucket,
            s3_key,
            ExtraArgs=extra_args if extra_args else None
        )
        return True

    def upload_video(self, local_path: Path, s3_key: str) -> str:
        """
        Upload a video file to S3 with video/mp4 content type.

        Args:
            local_path: Path to the local video file.
            s3_key: Destination key (path) in S3 bucket.

        Returns:
            The S3 key where the video was uploaded.
        """
        self._client.upload_file(
            str(local_path),
            self.bucket,
            s3_key,
            ExtraArgs={"ContentType": "video/mp4"}
        )
        return s3_key

    def download_file(self, s3_key: str, local_path: Path) -> None:
        """
        Download a file from S3 to local filesystem.

        Args:
            s3_key: S3 object key to download.
            local_path: Local path to save the downloaded file.

        Raises:
            S3ObjectNotFoundError: If the object does not exist in S3.
        """
        try:
            self._client.download_file(self.bucket, s3_key, str(local_path))
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                raise S3ObjectNotFoundError(f"Object not found: {s3_key}")
            raise

    def get_presigned_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for temporary access to an S3 object.

        Args:
            s3_key: S3 object key to generate URL for.
            expires_in: URL expiration time in seconds (default: 3600).

        Returns:
            Presigned URL string for accessing the object.
        """
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": s3_key},
            ExpiresIn=expires_in
        )

    def list_objects(self, prefix: str) -> List[Dict[str, Any]]:
        """
        List objects in S3 bucket matching a prefix.

        Args:
            prefix: S3 key prefix to filter objects.

        Returns:
            List of object metadata dictionaries.
        """
        response = self._client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        return response.get("Contents", [])

    def list_videos(self, coop_id: str) -> List[Dict[str, Any]]:
        """
        List video files for a specific coop.

        Args:
            coop_id: Identifier for the coop.

        Returns:
            List of video object metadata dictionaries.
        """
        prefix = f"videos/{coop_id}/"
        return self.list_objects(prefix)

    def delete_object(self, s3_key: str) -> bool:
        """
        Delete a single object from S3.

        Args:
            s3_key: S3 object key to delete.

        Returns:
            True if deletion succeeded.
        """
        self._client.delete_object(Bucket=self.bucket, Key=s3_key)
        return True

    def delete_objects(self, keys: List[str]) -> bool:
        """
        Delete multiple objects from S3 in a single request.

        Args:
            keys: List of S3 object keys to delete.

        Returns:
            True if deletion succeeded.
        """
        objects = [{"Key": key} for key in keys]
        self._client.delete_objects(
            Bucket=self.bucket,
            Delete={"Objects": objects}
        )
        return True
