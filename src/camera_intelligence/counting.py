"""Chicken counting module with detection, tracking, and multi-camera correlation."""

from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


@dataclass
class BoundingBox:
    """Axis-aligned bounding box defined by top-left corner and dimensions."""

    x: int
    y: int
    width: int
    height: int


@dataclass
class Detection:
    """A single chicken detection with bounding box and confidence score."""

    bbox: BoundingBox
    confidence: float


@dataclass
class TrackingResult:
    """Result of tracking a chicken across frames, including predicted position when lost."""

    track_id: str
    bbox: BoundingBox
    confidence: float
    status: str = "active"
    predicted_position: Optional[BoundingBox] = None


@dataclass
class CountResult:
    """Chicken count with confidence score and alert status."""

    count: int = 0
    confidence: float = 0.0
    low_confidence_alert: bool = False
    total_count: int = 0


@dataclass
class CameraTransitionEvent:
    """Event recording a tracked chicken moving between camera views."""

    leaving_camera: str
    entering_camera: str
    track_id: str
    direction: str


@dataclass
class FrameResult:
    """Aggregated tracking results for a single processed frame."""

    tracks: List[TrackingResult] = field(default_factory=list)


class ChickenCounter:
    """Detects, tracks, and counts chickens across camera frames.

    Uses brightness-based region detection with BFS flood-fill, nearest-neighbor
    tracking across frames, and multi-camera correlation to avoid double-counting.
    """

    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self._tracks: dict = {}
        self._next_track_id = 0
        self._last_detections: List[Detection] = []

    def _find_bright_regions(self, frame: np.ndarray) -> List[BoundingBox]:
        gray = np.mean(frame, axis=2)
        threshold = 128
        binary = gray > threshold

        if not np.any(binary):
            return []

        regions = []
        visited = np.zeros_like(binary, dtype=bool)

        while True:
            unvisited = binary & ~visited
            rows, cols = np.where(unvisited)
            if len(rows) == 0:
                break

            seed_r, seed_c = rows[0], cols[0]
            min_r, max_r = seed_r, seed_r
            min_c, max_c = seed_c, seed_c

            queue = deque([(seed_r, seed_c)])
            visited[seed_r, seed_c] = True

            while queue:
                r, c = queue.popleft()
                min_r = min(min_r, r)
                max_r = max(max_r, r)
                min_c = min(min_c, c)
                max_c = max(max_c, c)

                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < binary.shape[0] and 0 <= nc < binary.shape[1]:
                            if binary[nr, nc] and not visited[nr, nc]:
                                visited[nr, nc] = True
                                queue.append((nr, nc))

            width = max_c - min_c + 1
            height = max_r - min_r + 1
            if width > 5 and height > 5:
                regions.append(
                    BoundingBox(
                        x=int(min_c), y=int(min_r), width=int(width), height=int(height)
                    )
                )

        return regions

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Detect chickens in a frame, returning detections above the confidence threshold."""
        regions = self._find_bright_regions(frame)
        detections = []
        frame_area = frame.shape[0] * frame.shape[1]

        for region in regions:
            region_area = region.width * region.height
            coverage = region_area / frame_area
            aspect_ratio = region.width / max(region.height, 1)

            confidence = min(0.95, 0.5 + coverage * 5)
            if region.height < 60 or region.width < 60:
                confidence = min(confidence, 0.7)
            if aspect_ratio > 3 or aspect_ratio < 0.3:
                confidence *= 0.8

            if confidence >= self.confidence_threshold:
                detections.append(Detection(bbox=region, confidence=confidence))

        return detections

    def process_frame(self, frame: np.ndarray, frame_id: int) -> FrameResult:
        """Process a frame to detect and track chickens, matching to existing tracks."""
        detections = self.detect(frame)
        new_tracks = []
        matched_old_ids = set()
        matched_det_indices = set()

        for i, det in enumerate(detections):
            best_match = None
            best_dist = float("inf")

            for tid, info in self._tracks.items():
                if tid in matched_old_ids:
                    continue
                old_bbox = info["bbox"]
                dist = abs(det.bbox.x - old_bbox.x) + abs(det.bbox.y - old_bbox.y)
                if dist < best_dist and dist < 200:
                    best_dist = dist
                    best_match = tid

            if best_match is not None:
                matched_old_ids.add(best_match)
                matched_det_indices.add(i)
                self._tracks[best_match]["bbox"] = det.bbox
                self._tracks[best_match]["confidence"] = det.confidence
                self._tracks[best_match]["last_seen"] = frame_id
                new_tracks.append(
                    TrackingResult(
                        track_id=best_match,
                        bbox=det.bbox,
                        confidence=det.confidence,
                        status="active",
                    )
                )
            else:
                matched_det_indices.add(i)
                tid = f"track-{self._next_track_id}"
                self._next_track_id += 1
                self._tracks[tid] = {
                    "bbox": det.bbox,
                    "confidence": det.confidence,
                    "last_seen": frame_id,
                }
                new_tracks.append(
                    TrackingResult(
                        track_id=tid,
                        bbox=det.bbox,
                        confidence=det.confidence,
                        status="active",
                    )
                )

        for tid, info in self._tracks.items():
            if tid not in matched_old_ids and info["last_seen"] != frame_id:
                predicted = BoundingBox(
                    x=info["bbox"].x,
                    y=info["bbox"].y,
                    width=info["bbox"].width,
                    height=info["bbox"].height,
                )
                new_tracks.append(
                    TrackingResult(
                        track_id=tid,
                        bbox=info["bbox"],
                        confidence=0.0,
                        status="lost",
                        predicted_position=predicted,
                    )
                )

        return FrameResult(tracks=new_tracks)

    def count(self, frame: np.ndarray) -> CountResult:
        """Count chickens in a frame and return the count with confidence metrics."""
        detections = self.detect(frame)
        count = len(detections)

        if count == 0:
            confidence = 0.3
        else:
            avg_conf = sum(d.confidence for d in detections) / count
            confidence = avg_conf

        low_alert = confidence < self.confidence_threshold
        return CountResult(
            count=count,
            confidence=confidence,
            low_confidence_alert=low_alert,
            total_count=count,
        )

    def set_confidence_threshold(self, threshold: float):
        """Update the minimum confidence threshold for accepting detections."""
        self.confidence_threshold = threshold

    def correlate_counts(
        self, indoor: CountResult, outdoor: CountResult, overlap_estimate: int = 0
    ) -> CountResult:
        """Combine indoor and outdoor counts, subtracting estimated overlap."""
        total = indoor.count + outdoor.count - overlap_estimate
        avg_conf = (indoor.confidence + outdoor.confidence) / 2
        return CountResult(count=total, confidence=avg_conf, total_count=total)

    def detect_camera_transition(
        self, leaving_camera: str, entering_camera: str, track_id: str
    ) -> CameraTransitionEvent:
        """Record a chicken transitioning between two camera views."""
        direction = f"{leaving_camera}_to_{entering_camera}"
        return CameraTransitionEvent(
            leaving_camera=leaving_camera,
            entering_camera=entering_camera,
            track_id=track_id,
            direction=direction,
        )
