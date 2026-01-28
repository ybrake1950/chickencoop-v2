"""S3 client module for ChickenCoop."""
from .client import S3Client, S3ObjectNotFoundError

__all__ = ["S3Client", "S3ObjectNotFoundError"]
