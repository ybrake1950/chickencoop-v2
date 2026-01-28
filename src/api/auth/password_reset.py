"""Password reset token utilities."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

_reset_tokens: Dict[str, Dict[str, Any]] = {}


def generate_reset_token() -> str:
    """Generate a secure password reset token."""
    return secrets.token_urlsafe(32)


def store_reset_token(user_id: int, token: str, expires_hours: int = 1) -> None:
    """Store a password reset token with expiration."""
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    _reset_tokens[token] = {
        "user_id": user_id,
        "expires_at": expires_at,
    }


def validate_reset_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate a password reset token and return user info if valid."""
    token_data = _reset_tokens.get(token)
    if not token_data:
        return None

    if datetime.now(timezone.utc) >= token_data["expires_at"]:
        del _reset_tokens[token]
        return None

    return {"user_id": token_data["user_id"]}
