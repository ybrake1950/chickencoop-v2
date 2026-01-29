"""S3 presigned URL generation."""

import time
from urllib.parse import quote


class PresignedURLGenerator:
    """Generates S3 presigned URLs with security constraints."""

    def __init__(self, default_expiry_seconds: int = 900):
        self.default_expiry_seconds = default_expiry_seconds

    def generate_url(self, bucket: str, key: str, expiry_seconds: int = 0) -> str:
        """Generate a presigned S3 URL for the given bucket and key."""
        if expiry_seconds <= 0:
            expiry_seconds = self.default_expiry_seconds

        expires_at = int(time.time()) + expiry_seconds
        encoded_key = quote(key, safe="/")

        return (
            f"https://{bucket}.s3.amazonaws.com/{encoded_key}"
            f"?X-Amz-Expires={expiry_seconds}"
            f"&Expires={expires_at}"
        )
