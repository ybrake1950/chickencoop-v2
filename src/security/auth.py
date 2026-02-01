"""Authentication middleware and token validation."""

import hashlib
import hmac
import json
import base64
import time
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AuthResult:
    """Result of an authentication attempt."""

    authenticated: bool
    user_id: str = ""
    http_status_code: int = 200
    error: str = ""


class TokenValidator:
    """JWT-like token validator."""

    def __init__(self, secret_key: str, token_expiry_seconds: int = 3600):
        self._secret_key = secret_key
        self._token_expiry_seconds = token_expiry_seconds

    def generate_token(self, user_id: str) -> str:
        """Generate a signed token for the given user ID."""
        now = time.time()
        payload = {
            "user_id": user_id,
            "iat": now,
            "exp": now + self._token_expiry_seconds,
        }
        payload_bytes = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        signature = hmac.new(
            self._secret_key.encode(),
            payload_bytes.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"{payload_bytes}.{signature}"

    def validate_token(self, token: str) -> AuthResult:
        """Validate a token's signature and expiry, returning an AuthResult."""
        try:
            parts = token.split(".")
            if len(parts) != 2:
                return AuthResult(
                    authenticated=False,
                    http_status_code=401,
                    error="Invalid token format",
                )

            payload_bytes, signature = parts
            expected_sig = hmac.new(
                self._secret_key.encode(),
                payload_bytes.encode(),
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_sig):
                return AuthResult(
                    authenticated=False,
                    http_status_code=401,
                    error="Invalid token signature",
                )

            payload = json.loads(base64.urlsafe_b64decode(payload_bytes.encode()))

            if payload.get("exp", 0) < time.time():
                return AuthResult(
                    authenticated=False, http_status_code=401, error="Token expired"
                )

            return AuthResult(
                authenticated=True,
                user_id=payload.get("user_id", ""),
                http_status_code=200,
            )
        except (ValueError, KeyError, TypeError):
            return AuthResult(
                authenticated=False, http_status_code=401, error="Invalid token"
            )

    def refresh_token(self, old_token: str) -> Optional[str]:
        """Issue a new token if the old token has a valid signature."""
        result = self.validate_token(old_token)
        if not result.authenticated:
            # Still allow refresh if token structure is valid (even if expired)
            try:
                parts = old_token.split(".")
                if len(parts) != 2:
                    return None
                payload_bytes, signature = parts
                expected_sig = hmac.new(
                    self._secret_key.encode(),
                    payload_bytes.encode(),
                    hashlib.sha256,
                ).hexdigest()
                if not hmac.compare_digest(signature, expected_sig):
                    return None
                payload = json.loads(base64.urlsafe_b64decode(payload_bytes.encode()))
                user_id = payload.get("user_id")
                if user_id:
                    return self.generate_token(user_id)
            except (ValueError, KeyError, TypeError):
                return None
            return None
        return self.generate_token(result.user_id)


class AuthenticationMiddleware:
    """Authentication middleware for protecting routes."""

    def __init__(
        self,
        token_validator: TokenValidator,
        protected_paths: Optional[List[str]] = None,
    ):
        self._validator = token_validator
        self._protected_paths = protected_paths or []

    def is_protected(self, path: str) -> bool:
        """Return True if the given path requires authentication."""
        return path in self._protected_paths

    def authenticate(self, token: Optional[str]) -> AuthResult:
        """Authenticate a request using the provided token."""
        if token is None:
            return AuthResult(
                authenticated=False,
                http_status_code=401,
                error="Authentication required",
            )
        return self._validator.validate_token(token)
