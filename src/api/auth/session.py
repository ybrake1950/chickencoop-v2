"""Session management utilities."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

_sessions: Dict[str, Dict[str, Any]] = {}


def create_session(user_id: int, expires_in: int = 3600) -> Dict[str, Any]:
    """Create a new session for a user."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    session = {
        "token": token,
        "user_id": user_id,
        "expires_at": expires_at.isoformat(),
        "expiry": expires_at.isoformat(),
    }

    _sessions[token] = session
    return session


def get_session_user(token: str) -> Optional[int]:
    """Get the user ID associated with a session token."""
    session = _sessions.get(token)
    if session and is_session_valid(token):
        return session["user_id"]
    return None


def invalidate_session(token: str) -> None:
    """Invalidate a session by removing it."""
    if token in _sessions:
        del _sessions[token]


def is_session_valid(token: str) -> bool:
    """Check if a session token is valid and not expired."""
    session = _sessions.get(token)
    if not session:
        return False

    expires_at = datetime.fromisoformat(session["expires_at"])
    return datetime.now(timezone.utc) < expires_at
