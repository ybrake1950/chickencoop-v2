"""CSRF protection."""

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Optional


@dataclass
class CSRFToken:
    """A CSRF token."""

    value: str


@dataclass
class CSRFValidationResult:
    """Result of CSRF validation."""

    valid: bool
    error: str = ""


class CSRFProtection:
    """CSRF token generation and validation."""

    def __init__(self, secret_key: str):
        self._secret_key = secret_key
        self._tokens: dict[str, str] = {}

    def generate_token(self, session_id: str) -> CSRFToken:
        """Generate a new CSRF token for the given session."""
        nonce = secrets.token_hex(16)
        signature = hmac.new(
            self._secret_key.encode(),
            f"{session_id}:{nonce}".encode(),
            hashlib.sha256,
        ).hexdigest()
        token_value = f"{nonce}:{signature}"
        self._tokens[session_id] = token_value
        return CSRFToken(value=token_value)

    def validate_request(  # pylint: disable=unused-argument
        self,
        method: str,
        token: Optional[str],
        session_token: str,
        content_type: str = "",
    ) -> CSRFValidationResult:
        """Validate a CSRF token for a state-changing request."""
        # Safe methods don't need CSRF
        if method.upper() in ("GET", "HEAD", "OPTIONS"):
            return CSRFValidationResult(valid=True)

        if token is None:
            return CSRFValidationResult(valid=False, error="CSRF token required")

        # Verify the token matches what we generated for this session
        expected = self._tokens.get(session_token)
        if expected is None or not hmac.compare_digest(token, expected):
            return CSRFValidationResult(valid=False, error="Invalid CSRF token")

        return CSRFValidationResult(valid=True)
