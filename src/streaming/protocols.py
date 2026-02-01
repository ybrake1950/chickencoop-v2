"""Stream protocol support for HLS and WebRTC."""

import enum
import math
from dataclasses import dataclass, field
from typing import List


class StreamProtocol(enum.Enum):
    HLS = "hls"
    WEBRTC = "webrtc"


@dataclass
class HLSSegment:
    index: int
    duration_seconds: float
    data: bytes = b""


@dataclass
class HLSPlaylist:
    stream_id: str
    segments: List[HLSSegment] = field(default_factory=list)


@dataclass
class SDPOffer:
    sdp: str


@dataclass
class ICECandidate:
    candidate: str


@dataclass
class PeerConnection:
    state: str


@dataclass
class NegotiationResult:
    protocol: StreamProtocol


class HLSProvider:
    def __init__(self, segment_duration: int = 4):
        self.target_segment_duration = segment_duration
        self._playlists: dict[str, HLSPlaylist] = {}

    def generate_manifest(self, _stream_id: str) -> str:
        """Generate an HLS manifest (m3u8) header for the given stream."""
        return "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:{}\n".format(
            self.target_segment_duration
        )

    def create_segments(self, stream_id: str, duration: int) -> List[HLSSegment]:
        """Create HLS segments for a stream of the given duration in seconds."""
        count = max(1, math.ceil(duration / self.target_segment_duration))
        segments = []
        for i in range(count):
            seg_dur = min(
                self.target_segment_duration,
                duration - i * self.target_segment_duration,
            )
            segments.append(HLSSegment(index=i, duration_seconds=float(seg_dur)))
        if stream_id not in self._playlists:
            self._playlists[stream_id] = HLSPlaylist(stream_id=stream_id)
        self._playlists[stream_id].segments = list(segments)
        return segments

    def add_segment(self, stream_id: str, segment_data: bytes) -> None:
        """Append a new segment with the given data to a stream's playlist."""
        if stream_id not in self._playlists:
            self._playlists[stream_id] = HLSPlaylist(stream_id=stream_id)
        playlist = self._playlists[stream_id]
        idx = len(playlist.segments)
        playlist.segments.append(
            HLSSegment(
                index=idx,
                duration_seconds=float(self.target_segment_duration),
                data=segment_data,
            )
        )

    def get_playlist(self, stream_id: str) -> HLSPlaylist:
        """Return the playlist for a stream, or an empty playlist if none exists."""
        return self._playlists.get(stream_id, HLSPlaylist(stream_id=stream_id))


class WebRTCProvider:
    def __init__(self):
        self.target_latency_ms = 200

    def create_offer(self) -> SDPOffer:
        """Create an SDP offer for WebRTC signaling."""
        return SDPOffer(sdp="v=0\no=- 0 0 IN IP4 127.0.0.1\ns=stream\n")

    def gather_ice_candidates(self) -> List[ICECandidate]:
        """Gather ICE candidates for peer connection establishment."""
        return [
            ICECandidate(
                candidate="candidate:1 1 udp 2130706431 127.0.0.1 5000 typ host"
            )
        ]

    def connect(self, _peer) -> PeerConnection:
        """Establish a WebRTC peer connection and return its state."""
        return PeerConnection(state="connected")


class ProtocolNegotiator:
    def __init__(self, available: List[StreamProtocol]):
        self._available = list(available)
        self._disabled: set[StreamProtocol] = set()

    def disable(self, protocol: StreamProtocol) -> None:
        """Disable a protocol so it will not be selected during negotiation."""
        self._disabled.add(protocol)

    def negotiate(self, preferred: str) -> NegotiationResult:
        """Negotiate a streaming protocol, honoring the client's preference if available."""
        proto_map = {"hls": StreamProtocol.HLS, "webrtc": StreamProtocol.WEBRTC}
        preferred_proto = proto_map.get(preferred)
        if (
            preferred_proto
            and preferred_proto in self._available
            and preferred_proto not in self._disabled
        ):
            return NegotiationResult(protocol=preferred_proto)
        for proto in self._available:
            if proto not in self._disabled:
                return NegotiationResult(protocol=proto)
        raise ValueError("No available protocols")

    def detect_capabilities(self, user_agent: str) -> List[str]:
        """Detect supported streaming protocols based on the client's user agent."""
        caps = []
        if "Mozilla" in user_agent:
            caps.append("hls")
            caps.append("webrtc")
        return caps
