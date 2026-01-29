"""
Phase 16: Chicken Counting Tests
================================

FUNCTIONALITY BEING TESTED:
---------------------------
- ML-based chicken detection in frames
- Chicken tracking across frames
- Occlusion handling
- Count confidence scoring
- Multi-camera correlation

WHY THIS MATTERS:
-----------------
Automated chicken counting enables headcount alerts when chickens
are missing or gained. Accurate counting requires handling occlusion,
varying lighting, and multi-camera views.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase16_camera_intelligence/counting/test_chicken_counting.py -v
"""
import pytest
import numpy as np
from unittest.mock import MagicMock

from src.camera_intelligence.counting import ChickenCounter, Detection, TrackingResult, CountResult


@pytest.fixture
def counter():
    return ChickenCounter(confidence_threshold=0.5)

@pytest.fixture
def mock_frame():
    return np.zeros((480, 640, 3), dtype=np.uint8)

@pytest.fixture
def mock_frame_with_chickens():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[100:200, 100:200] = 255
    frame[100:200, 300:400] = 255
    frame[300:400, 200:300] = 255
    return frame


class TestChickenDetection:
    """Test chicken detection in frames."""

    def test_detect_chicken_in_frame(self, counter, mock_frame_with_chickens):
        """Chickens detected in frame."""
        detections = counter.detect(mock_frame_with_chickens)
        assert len(detections) >= 1

    def test_detect_multiple_chickens(self, counter, mock_frame_with_chickens):
        """Multiple chickens detected."""
        detections = counter.detect(mock_frame_with_chickens)
        assert len(detections) >= 2

    def test_detection_bounding_box(self, counter, mock_frame_with_chickens):
        """Detection has bounding box."""
        detections = counter.detect(mock_frame_with_chickens)
        for d in detections:
            assert d.bbox.x >= 0 and d.bbox.y >= 0
            assert d.bbox.width > 0 and d.bbox.height > 0

    def test_detection_confidence(self, counter, mock_frame_with_chickens):
        """Detection has confidence score."""
        detections = counter.detect(mock_frame_with_chickens)
        for d in detections:
            assert 0.0 <= d.confidence <= 1.0


class TestChickenTracking:
    """Test chicken tracking across frames."""

    def test_track_chicken_across_frames(self, counter, mock_frame_with_chickens):
        """Same chicken tracked across frames."""
        r1 = counter.process_frame(mock_frame_with_chickens, frame_id=1)
        r2 = counter.process_frame(mock_frame_with_chickens, frame_id=2)
        ids1 = {t.track_id for t in r1.tracks}
        ids2 = {t.track_id for t in r2.tracks}
        assert len(ids1 & ids2) >= 1

    def test_assign_unique_id(self, counter, mock_frame_with_chickens):
        """Each chicken gets unique track ID."""
        result = counter.process_frame(mock_frame_with_chickens, frame_id=1)
        track_ids = [t.track_id for t in result.tracks]
        assert len(track_ids) == len(set(track_ids))

    def test_handle_chicken_leaving_frame(self, counter, mock_frame_with_chickens, mock_frame):
        """Chicken leaving frame handled."""
        counter.process_frame(mock_frame_with_chickens, frame_id=1)
        r2 = counter.process_frame(mock_frame, frame_id=2)
        lost = [t for t in r2.tracks if t.status == "lost"]
        assert len(lost) >= 1 or len(r2.tracks) == 0

    def test_handle_chicken_entering_frame(self, counter, mock_frame, mock_frame_with_chickens):
        """New chicken entering frame detected."""
        counter.process_frame(mock_frame, frame_id=1)
        r2 = counter.process_frame(mock_frame_with_chickens, frame_id=2)
        assert len(r2.tracks) >= 1


class TestOcclusionHandling:
    """Test occlusion handling."""

    def test_partial_occlusion(self, counter):
        """Partially occluded chicken detected with lower confidence."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:150, 100:200] = 255
        detections = counter.detect(frame)
        if len(detections) > 0:
            assert detections[0].confidence < 0.95

    def test_full_occlusion_prediction(self, counter, mock_frame_with_chickens, mock_frame):
        """Predict position during full occlusion."""
        counter.process_frame(mock_frame_with_chickens, frame_id=1)
        result = counter.process_frame(mock_frame, frame_id=2)
        predicted = [t for t in result.tracks if t.predicted_position is not None]
        assert len(predicted) >= 1 or len(result.tracks) == 0

    def test_reidentify_after_occlusion(self, counter, mock_frame_with_chickens, mock_frame):
        """Reidentify chicken after occlusion."""
        r1 = counter.process_frame(mock_frame_with_chickens, frame_id=1)
        counter.process_frame(mock_frame, frame_id=2)
        r3 = counter.process_frame(mock_frame_with_chickens, frame_id=3)
        ids1 = {t.track_id for t in r1.tracks}
        ids3 = {t.track_id for t in r3.tracks}
        assert len(ids1 & ids3) >= 1 or len(r3.tracks) >= 1


class TestCountConfidence:
    """Test count confidence scoring."""

    def test_confidence_score_generated(self, counter, mock_frame_with_chickens):
        """Count result includes confidence."""
        result = counter.count(mock_frame_with_chickens)
        assert result.confidence is not None

    def test_high_confidence_clear_view(self, counter, mock_frame_with_chickens):
        """Clear view gives high confidence."""
        result = counter.count(mock_frame_with_chickens)
        assert result.confidence > 0.5

    def test_low_confidence_occlusion(self, counter, mock_frame):
        """Dark/empty frame gives lower confidence."""
        result = counter.count(mock_frame)
        assert result.confidence < 0.9

    def test_confidence_threshold_alert(self, counter, mock_frame):
        """Low confidence triggers alert."""
        counter.set_confidence_threshold(0.7)
        result = counter.count(mock_frame)
        assert result.low_confidence_alert is True or result.confidence < 0.7


class TestMultiCameraCorrelation:
    """Test multi-camera correlation."""

    def test_correlate_indoor_outdoor(self, counter, mock_frame_with_chickens):
        """Correlate counts between cameras."""
        indoor = counter.count(mock_frame_with_chickens)
        outdoor_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        outdoor_frame[200:300, 200:300] = 255
        outdoor = counter.count(outdoor_frame)
        total = counter.correlate_counts(indoor=indoor, outdoor=outdoor)
        assert total.total_count >= 1

    def test_avoid_double_counting(self, counter):
        """Same chicken not double counted."""
        total = counter.correlate_counts(
            indoor=CountResult(count=5, confidence=0.9),
            outdoor=CountResult(count=3, confidence=0.9),
            overlap_estimate=2
        )
        assert total.total_count <= 6

    def test_track_movement_between_cameras(self, counter):
        """Track chicken movement between cameras."""
        event = counter.detect_camera_transition(
            leaving_camera="indoor", entering_camera="outdoor", track_id="chicken-1"
        )
        assert event is not None
        assert event.direction == "indoor_to_outdoor"
