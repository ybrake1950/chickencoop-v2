"""
Phase 15: Stream Protocols Tests
================================

FUNCTIONALITY BEING TESTED:
---------------------------
- HLS (HTTP Live Streaming) support
- WebRTC support for low latency
- Protocol negotiation
- Fallback mechanisms

WHY THIS MATTERS:
-----------------
Different clients support different streaming protocols. HLS is widely
supported but has latency. WebRTC enables low-latency streaming.
Proper protocol support ensures compatibility.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase15_streaming/protocols/test_stream_protocols.py -v
"""
import pytest
from unittest.mock import MagicMock

from src.streaming.protocols import HLSProvider, WebRTCProvider, ProtocolNegotiator, StreamProtocol


@pytest.fixture
def hls_provider():
    return HLSProvider(segment_duration=4)

@pytest.fixture
def webrtc_provider():
    return WebRTCProvider()

@pytest.fixture
def negotiator():
    return ProtocolNegotiator(available=[StreamProtocol.HLS, StreamProtocol.WEBRTC])


class TestHLSSupport:
    """Test HLS streaming support."""

    def test_hls_manifest_generated(self, hls_provider):
        """HLS manifest (.m3u8) generated."""
        manifest = hls_provider.generate_manifest("stream-1")
        assert "#EXTM3U" in manifest or manifest.endswith(".m3u8")

    def test_hls_segments_created(self, hls_provider):
        """HLS segments (.ts) created."""
        segments = hls_provider.create_segments("stream-1", duration=10)
        assert len(segments) > 0

    def test_hls_segment_duration(self, hls_provider):
        """HLS segment duration appropriate."""
        segments = hls_provider.create_segments("stream-1", duration=20)
        for seg in segments:
            assert seg.duration_seconds <= hls_provider.target_segment_duration + 1

    def test_hls_playlist_updated(self, hls_provider):
        """HLS playlist updated with new segments."""
        hls_provider.create_segments("stream-1", duration=4)
        hls_provider.add_segment("stream-1", segment_data=b"new-segment")
        playlist = hls_provider.get_playlist("stream-1")
        assert len(playlist.segments) >= 2


class TestWebRTCSupport:
    """Test WebRTC streaming support."""

    def test_webrtc_signaling(self, webrtc_provider):
        """WebRTC signaling works."""
        offer = webrtc_provider.create_offer()
        assert offer.sdp is not None

    def test_webrtc_ice_candidates(self, webrtc_provider):
        """ICE candidates exchanged."""
        candidates = webrtc_provider.gather_ice_candidates()
        assert len(candidates) > 0

    def test_webrtc_connection_established(self, webrtc_provider):
        """WebRTC connection established."""
        peer = MagicMock()
        connection = webrtc_provider.connect(peer)
        assert connection.state == "connected"

    def test_webrtc_low_latency(self, webrtc_provider):
        """WebRTC achieves low latency."""
        assert webrtc_provider.target_latency_ms < 500


class TestProtocolNegotiation:
    """Test protocol negotiation."""

    def test_client_preference_respected(self, negotiator):
        """Client protocol preference respected."""
        result = negotiator.negotiate(preferred="webrtc")
        assert result.protocol == StreamProtocol.WEBRTC

    def test_fallback_to_hls(self, negotiator):
        """Fallback to HLS if WebRTC fails."""
        negotiator.disable(StreamProtocol.WEBRTC)
        result = negotiator.negotiate(preferred="webrtc")
        assert result.protocol == StreamProtocol.HLS

    def test_capability_detection(self, negotiator):
        """Client capabilities detected."""
        caps = negotiator.detect_capabilities(user_agent="Mozilla/5.0")
        assert "hls" in caps or "webrtc" in caps
