"""AWS integration package for ChickenCoop."""
from .iot import IoTClient
from .s3 import S3Client, S3ObjectNotFoundError
from .sns import SNSClient, SNSPublishError, InvalidEmailError

__all__ = [
    "IoTClient",
    "S3Client",
    "S3ObjectNotFoundError",
    "SNSClient",
    "SNSPublishError",
    "InvalidEmailError",
]
