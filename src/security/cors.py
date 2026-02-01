"""CORS configuration and validation."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class CORSConfig:
    """CORS configuration."""

    allowed_origins: List[str] = field(default_factory=list)
    allowed_methods: List[str] = field(default_factory=lambda: ["GET"])
    allowed_headers: List[str] = field(default_factory=list)
    allow_credentials: bool = False
    max_age: int = 3600


class CORSValidator:
    """Validates CORS requests against configuration."""

    def __init__(self, config: CORSConfig):
        self.config = config

    def is_origin_allowed(self, origin: str) -> bool:
        """Return True if the origin is in the allowed origins list."""
        return origin in self.config.allowed_origins

    def is_method_allowed(self, method: str) -> bool:
        """Return True if the HTTP method is in the allowed methods list."""
        return method in self.config.allowed_methods

    def get_cors_headers(self, origin: str) -> Dict[str, str]:
        """Build CORS response headers for the given origin."""
        headers: Dict[str, str] = {}
        if self.is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
        if self.config.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        return headers

    def get_preflight_headers(  # pylint: disable=unused-argument
        self, origin: str, request_method: str, request_headers: str
    ) -> Dict[str, str]:
        """Build CORS preflight response headers including allowed methods and max age."""
        headers = self.get_cors_headers(origin)
        headers["Access-Control-Allow-Methods"] = ", ".join(self.config.allowed_methods)
        headers["Access-Control-Allow-Headers"] = request_headers
        headers["Access-Control-Max-Age"] = str(self.config.max_age)
        return headers
