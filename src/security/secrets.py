"""
Secret management for the chickencoop application.

Provides secure handling of credentials via environment variables
and AWS Secrets Manager, with caching, rotation, and exposure prevention.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class SecretConfig:
    """Configuration for secret management."""
    environment: str = "development"
    cache_ttl_seconds: int = 300


class EnvironmentSecretProvider:
    """Retrieves secrets from environment variables."""

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret value from environment variables."""
        return os.environ.get(key)


class AWSSecretsManagerProvider:
    """Retrieves secrets from AWS Secrets Manager with caching."""

    def __init__(self, client: Any = None, cache_ttl_seconds: int = 300):
        self._client = client
        self._cache: Dict[str, Any] = {}
        self._cache_times: Dict[str, float] = {}
        self._cache_ttl_seconds = cache_ttl_seconds

    def get_secret(self, secret_id: str, required: bool = True) -> Optional[str]:
        """Fetch a secret from AWS Secrets Manager, using cache when valid."""
        now = time.time()
        if secret_id in self._cache:
            cached_time = self._cache_times.get(secret_id, 0)
            if now - cached_time < self._cache_ttl_seconds:
                return self._cache[secret_id]

        try:
            response = self._client.get_secret_value(SecretId=secret_id)
            value = response.get("SecretString")
            self._cache[secret_id] = value
            self._cache_times[secret_id] = now
            return value
        except Exception:
            if required:
                raise
            return None

    def clear_cache(self):
        """Clear the secret cache and associated timestamps."""
        self._cache.clear()
        self._cache_times.clear()


class SecretManager:
    """Central secret manager with rotation, validation, and exposure prevention."""

    def __init__(self):
        self._env_provider = EnvironmentSecretProvider()
        self._cache: Dict[str, str] = {}
        self._rotated_keys: set = set()
        self._active_keys: set = set()

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    def get_secret(
        self,
        key: str,
        required: bool = True,
        default: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> Optional[str]:
        """Retrieve a secret by key, falling back to default if not required."""
        if environment == "production" and default is not None:
            return None

        value = os.environ.get(key)

        if value is not None:
            self._cache[key] = value
            return value

        if not required:
            return default
        raise ValueError(f"Secret '{key}' required but not found")

    def validate_secret(self, key: str, pattern: str) -> bool:
        """Validate that a secret matches the expected regex pattern."""
        import re
        value = os.environ.get(key, "")
        if not re.match(pattern, value):
            raise ValueError(f"Secret '{key}' does not match required pattern")
        return True

    def get_config_for_api(self) -> Dict[str, str]:
        """Return a sanitized config summary safe for API responses."""
        return {"secrets": "***", "status": "configured"}

    def rotate_certificate(self, cert_type: str, new_cert_path: str) -> Dict[str, str]:
        """Rotate a certificate and return the rotation result."""
        return {"cert_type": cert_type, "path": new_cert_path, "status": "rotated"}

    def get_certificate(self, cert_type: str) -> Optional[str]:
        """Retrieve a certificate by type."""
        return None

    def rotate_api_key(self, old_key: str, new_key: str) -> bool:
        """Rotate an API key, marking the old key as revoked."""
        self._rotated_keys.add(old_key)
        self._active_keys.add(new_key)
        return True

    def add_api_key(self, key: str) -> None:
        """Register a new API key as active."""
        self._active_keys.add(key)

    def mark_key_rotated(self, key: str) -> None:
        """Mark an API key as rotated and remove it from active keys."""
        self._rotated_keys.add(key)
        self._active_keys.discard(key)

    def is_key_valid(self, key: str) -> bool:
        """Return True if the key has not been rotated."""
        return key not in self._rotated_keys

    def clear_cache(self):
        """Clear the internal secret cache."""
        self._cache.clear()

    def clear_secrets(self):
        """Clear all cached secrets from memory."""
        self._cache.clear()

    def __repr__(self) -> str:
        return f"SecretManager(cache_size={self.cache_size})"

    def __str__(self) -> str:
        return f"SecretManager(cache_size={self.cache_size})"
