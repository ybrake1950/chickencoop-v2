"""Rate limiting for API endpoints."""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    endpoint_name: str = ""
    use_user_id: bool = False


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    http_status_code: int = 200
    retry_after_seconds: int = 0


class RateLimiter:
    """Token-bucket style rate limiter per client."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._requests: Dict[str, List[float]] = {}

    def check_rate_limit(
        self, client_id: str, user_id: Optional[str] = None
    ) -> RateLimitResult:
        """Check whether a request from the given client is within rate limits."""
        key = user_id if self.config.use_user_id and user_id else client_id
        now = time.monotonic()
        window = 60.0  # 1-minute window

        if key not in self._requests:
            self._requests[key] = []

        # Prune old entries outside the window
        self._requests[key] = [t for t in self._requests[key] if now - t < window]

        if len(self._requests[key]) >= self.config.requests_per_minute:
            oldest = self._requests[key][0]
            retry_after = int(window - (now - oldest)) + 1
            return RateLimitResult(
                allowed=False,
                http_status_code=429,
                retry_after_seconds=max(1, min(retry_after, 60)),
            )

        self._requests[key].append(now)
        return RateLimitResult(allowed=True)
