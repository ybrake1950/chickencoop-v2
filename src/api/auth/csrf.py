"""CSRF protection utilities."""

import secrets
from typing import Optional

_valid_tokens: set = set()


def generate_csrf_token() -> str:
    """Generate a new CSRF token."""
    token = secrets.token_urlsafe(32)
    _valid_tokens.add(token)
    return token


def validate_csrf_token(token: Optional[str]) -> bool:
    """Validate a CSRF token."""
    if not token or token == "":
        return False
    return token in _valid_tokens
