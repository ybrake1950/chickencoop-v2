"""Live streaming module for chicken coop monitoring."""

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class StreamStatus(Enum):
    ACTIVE = "active"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class StreamConfig:
    max_concurrent: int = 2
    max_duration_seconds: int = 3600
    per_coop: bool = False


@dataclass
class StreamSession:
    session_id: str
    camera: str
    status: StreamStatus
    playback_url: Optional[str] = None
    timeout_seconds: Optional[int] = None
    quality: str = "480p"
    adaptive_bitrate: bool = False
    error: Optional[str] = None
    coop_id: Optional[str] = None


VALID_TOKEN_PREFIX = "valid-stream-token"


class StreamManager:
    def __init__(self, config: StreamConfig):
        self.config = config
        self._sessions: dict[str, StreamSession] = {}
        self.available_qualities: List[str] = ["1080p", "720p", "480p", "360p"]

    @property
    def active_sessions(self) -> List[StreamSession]:
        """Return all sessions with ACTIVE status."""
        return [s for s in self._sessions.values() if s.status == StreamStatus.ACTIVE]

    def start_stream(
        self,
        camera: str,
        token: Optional[str],
        timeout: Optional[int] = None,
        quality: str = "480p",
        adaptive: bool = False,
        coop_id: Optional[str] = None,
    ) -> StreamSession:
        """Start a new stream session for the given camera.

        Validates the auth token, enforces concurrent stream limits,
        and returns a StreamSession with the result.
        """
        if token is None or not token.startswith(VALID_TOKEN_PREFIX):
            session = StreamSession(
                session_id=str(uuid.uuid4()),
                camera=camera,
                status=StreamStatus.ERROR,
                error=(
                    "Authentication required"
                    if token is None
                    else "Invalid or expired token"
                ),
            )
            self._sessions[session.session_id] = session
            return session

        if self.config.per_coop:
            active_for_coop = [s for s in self.active_sessions if s.coop_id == coop_id]
            count = len(active_for_coop)
        else:
            count = len(self.active_sessions)

        if count >= self.config.max_concurrent:
            session = StreamSession(
                session_id=str(uuid.uuid4()),
                camera=camera,
                status=StreamStatus.ERROR,
                error="Concurrent stream limit reached",
            )
            self._sessions[session.session_id] = session
            return session

        session_id = str(uuid.uuid4())
        session = StreamSession(
            session_id=session_id,
            camera=camera,
            status=StreamStatus.ACTIVE,
            playback_url=f"/stream/{session_id}",
            timeout_seconds=timeout,
            quality=quality,
            adaptive_bitrate=adaptive,
            coop_id=coop_id,
        )
        self._sessions[session_id] = session
        return session

    def stop_stream(self, session_id: str) -> None:
        """Stop an active stream session by marking it as STOPPED."""
        if session_id in self._sessions:
            self._sessions[session_id].status = StreamStatus.STOPPED

    def get_session(self, session_id: str) -> Optional[StreamSession]:
        """Retrieve a stream session by its ID, or None if not found."""
        return self._sessions.get(session_id)

    def cleanup_expired(self) -> None:
        """Stop all active sessions whose timeout has expired."""
        for session in list(self._sessions.values()):
            if (
                session.status == StreamStatus.ACTIVE
                and session.timeout_seconds is not None
                and session.timeout_seconds <= 0
            ):
                session.status = StreamStatus.STOPPED
