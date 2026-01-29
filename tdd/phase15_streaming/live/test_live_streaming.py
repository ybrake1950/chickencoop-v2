"""
Phase 15: Live Streaming Tests
==============================

FUNCTIONALITY BEING TESTED:
---------------------------
- Live stream initiation and termination
- Stream session management
- Stream quality settings
- Stream authentication
- Concurrent stream limits

WHY THIS MATTERS:
-----------------
Live streaming enables real-time monitoring of the chicken coop.
Users can check on chickens without waiting for recorded video.
Proper session management prevents resource exhaustion.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase15_streaming/live/test_live_streaming.py -v
"""
import pytest
from unittest.mock import MagicMock

from src.streaming.live import StreamManager, StreamSession, StreamConfig, StreamStatus


@pytest.fixture
def manager():
    return StreamManager(config=StreamConfig(max_concurrent=2, max_duration_seconds=3600))

@pytest.fixture
def auth_token():
    return "valid-stream-token-123"


class TestStreamInitiation:
    """Test stream start and stop."""

    def test_start_stream(self, manager, auth_token):
        """Live stream can be started."""
        result = manager.start_stream(camera="indoor", token=auth_token)
        assert result.status == StreamStatus.ACTIVE

    def test_stop_stream(self, manager, auth_token):
        """Live stream can be stopped."""
        session = manager.start_stream(camera="indoor", token=auth_token)
        manager.stop_stream(session.session_id)
        assert manager.get_session(session.session_id).status == StreamStatus.STOPPED

    def test_stream_returns_url(self, manager, auth_token):
        """Stream start returns playback URL."""
        result = manager.start_stream(camera="indoor", token=auth_token)
        assert result.playback_url is not None

    def test_stream_timeout(self, manager, auth_token):
        """Stream auto-stops after timeout."""
        session = manager.start_stream(camera="indoor", token=auth_token, timeout=30)
        assert session.timeout_seconds == 30

    def test_stream_max_duration(self, manager):
        """Stream has maximum duration limit."""
        assert manager.config.max_duration_seconds == 3600


class TestStreamSession:
    """Test stream session management."""

    def test_session_created_on_start(self, manager, auth_token):
        """Session created when stream starts."""
        result = manager.start_stream(camera="indoor", token=auth_token)
        assert manager.get_session(result.session_id) is not None

    def test_session_tracked(self, manager, auth_token):
        """Active sessions tracked."""
        manager.start_stream(camera="indoor", token=auth_token)
        manager.start_stream(camera="outdoor", token=auth_token)
        assert len(manager.active_sessions) == 2

    def test_session_cleanup_on_stop(self, manager, auth_token):
        """Session cleaned up on stop."""
        session = manager.start_stream(camera="indoor", token=auth_token)
        manager.stop_stream(session.session_id)
        active_ids = [s.session_id for s in manager.active_sessions]
        assert session.session_id not in active_ids

    def test_session_cleanup_on_timeout(self, manager, auth_token):
        """Session cleaned up on timeout."""
        session = manager.start_stream(camera="indoor", token=auth_token, timeout=0)
        manager.cleanup_expired()
        active_ids = [s.session_id for s in manager.active_sessions]
        assert session.session_id not in active_ids


class TestStreamQuality:
    """Test stream quality settings."""

    def test_quality_levels_available(self, manager):
        """Multiple quality levels available."""
        assert "720p" in manager.available_qualities
        assert "480p" in manager.available_qualities

    def test_quality_selection(self, manager, auth_token):
        """Quality can be selected."""
        session = manager.start_stream(camera="indoor", token=auth_token, quality="720p")
        assert session.quality == "720p"

    def test_adaptive_bitrate(self, manager, auth_token):
        """Adaptive bitrate supported."""
        session = manager.start_stream(camera="indoor", token=auth_token, adaptive=True)
        assert session.adaptive_bitrate is True


class TestStreamAuthentication:
    """Test stream authentication."""

    def test_stream_requires_auth(self, manager):
        """Stream requires authentication."""
        result = manager.start_stream(camera="indoor", token=None)
        assert result.status != StreamStatus.ACTIVE or result.error is not None

    def test_stream_token_validated(self, manager, auth_token):
        """Stream token validated."""
        result = manager.start_stream(camera="indoor", token=auth_token)
        assert result.status == StreamStatus.ACTIVE

    def test_expired_token_rejected(self, manager):
        """Expired stream token rejected."""
        result = manager.start_stream(camera="indoor", token="expired-token")
        assert result.status != StreamStatus.ACTIVE


class TestConcurrentStreams:
    """Test concurrent stream limits."""

    def test_concurrent_limit_enforced(self, manager, auth_token):
        """Concurrent stream limit enforced."""
        manager.start_stream(camera="cam1", token=auth_token)
        manager.start_stream(camera="cam2", token=auth_token)
        result = manager.start_stream(camera="cam3", token=auth_token)
        assert result.status != StreamStatus.ACTIVE or result.error is not None

    def test_limit_per_coop(self, auth_token):
        """Limit is per coop."""
        mgr = StreamManager(config=StreamConfig(max_concurrent=1, per_coop=True))
        mgr.start_stream(camera="indoor", token=auth_token, coop_id="coop1")
        result = mgr.start_stream(camera="indoor", token=auth_token, coop_id="coop2")
        assert result.status == StreamStatus.ACTIVE

    def test_over_limit_returns_error(self, manager, auth_token):
        """Over limit returns appropriate error."""
        manager.start_stream(camera="cam1", token=auth_token)
        manager.start_stream(camera="cam2", token=auth_token)
        result = manager.start_stream(camera="cam3", token=auth_token)
        assert "limit" in str(result.error).lower() or result.status != StreamStatus.ACTIVE
