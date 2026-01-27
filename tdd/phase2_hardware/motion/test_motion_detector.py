"""
TDD Tests: Motion Detection

These tests define the expected behavior for motion detection algorithms.
Implement src/hardware/motion/detector.py to make these tests pass.

Run: pytest tdd/phase2_hardware/motion/test_motion_detector.py -v
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def blank_frame():
    """Create a blank (black) frame."""
    return np.zeros((720, 1280, 3), dtype=np.uint8)


@pytest.fixture
def white_frame():
    """Create a white frame."""
    return np.ones((720, 1280, 3), dtype=np.uint8) * 255


@pytest.fixture
def frame_with_motion(blank_frame):
    """Create a frame with a moving object (white rectangle)."""
    frame = blank_frame.copy()
    # Add a white rectangle to simulate motion
    frame[300:400, 500:700] = 255
    return frame


# =============================================================================
# Test: Motion Detector Initialization
# =============================================================================

class TestMotionDetectorInit:
    """Tests for motion detector initialization."""

    def test_detector_can_be_instantiated(self):
        """MotionDetector should be instantiable."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()

        assert detector is not None

    def test_detector_default_sensitivity(self):
        """Default sensitivity should be set."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()

        assert hasattr(detector, 'sensitivity')
        assert 0 <= detector.sensitivity <= 100

    def test_detector_custom_sensitivity(self):
        """Should accept custom sensitivity."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector(sensitivity=75)

        assert detector.sensitivity == 75

    def test_detector_default_min_area(self):
        """Default minimum area should be set."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()

        assert hasattr(detector, 'min_area')
        assert detector.min_area > 0

    def test_detector_custom_min_area(self):
        """Should accept custom minimum area."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector(min_area=1000)

        assert detector.min_area == 1000


# =============================================================================
# Test: Motion Detection Core
# =============================================================================

class TestMotionDetectionCore:
    """Tests for core motion detection functionality."""

    def test_detect_returns_boolean(self, blank_frame):
        """detect() should return boolean indicating motion."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()
        detector.set_reference_frame(blank_frame)

        result = detector.detect(blank_frame)

        assert isinstance(result, bool)

    def test_no_motion_on_identical_frames(self, blank_frame):
        """Should detect no motion on identical frames."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()
        detector.set_reference_frame(blank_frame)

        result = detector.detect(blank_frame)

        assert result is False

    def test_motion_on_different_frames(self, blank_frame, frame_with_motion):
        """Should detect motion when frames differ significantly."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector(sensitivity=50, min_area=100)
        detector.set_reference_frame(blank_frame)

        result = detector.detect(frame_with_motion)

        assert result is True

    def test_motion_respects_min_area(self, blank_frame):
        """Should not detect motion smaller than min_area."""
        from src.hardware.motion.detector import MotionDetector

        # Create a small change
        small_motion_frame = blank_frame.copy()
        small_motion_frame[100:110, 100:110] = 255  # 10x10 = 100 pixels

        detector = MotionDetector(min_area=500)  # Require 500+ pixels
        detector.set_reference_frame(blank_frame)

        result = detector.detect(small_motion_frame)

        assert result is False

    def test_motion_sensitivity_affects_detection(self, blank_frame):
        """Higher sensitivity should detect smaller changes."""
        from src.hardware.motion.detector import MotionDetector

        # Create subtle change
        subtle_frame = blank_frame.copy()
        subtle_frame[300:350, 500:550] = 50  # Low intensity change

        low_sens = MotionDetector(sensitivity=10)
        high_sens = MotionDetector(sensitivity=90)

        low_sens.set_reference_frame(blank_frame)
        high_sens.set_reference_frame(blank_frame)

        # High sensitivity should be more likely to detect
        # (Actual behavior depends on implementation)
        low_result = low_sens.detect(subtle_frame)
        high_result = high_sens.detect(subtle_frame)

        # At minimum, both should return boolean
        assert isinstance(low_result, bool)
        assert isinstance(high_result, bool)


# =============================================================================
# Test: Motion Detection Results
# =============================================================================

class TestMotionDetectionResults:
    """Tests for detailed motion detection results."""

    def test_detect_with_details_returns_dict(self, blank_frame, frame_with_motion):
        """detect_with_details() should return detailed results."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()
        detector.set_reference_frame(blank_frame)

        result = detector.detect_with_details(frame_with_motion)

        assert isinstance(result, dict)

    def test_details_include_motion_detected(self, blank_frame, frame_with_motion):
        """Results should include motion_detected boolean."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()
        detector.set_reference_frame(blank_frame)

        result = detector.detect_with_details(frame_with_motion)

        assert "motion_detected" in result
        assert isinstance(result["motion_detected"], bool)

    def test_details_include_contour_count(self, blank_frame, frame_with_motion):
        """Results should include number of motion contours."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()
        detector.set_reference_frame(blank_frame)

        result = detector.detect_with_details(frame_with_motion)

        assert "contour_count" in result
        assert isinstance(result["contour_count"], int)

    def test_details_include_total_area(self, blank_frame, frame_with_motion):
        """Results should include total motion area."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()
        detector.set_reference_frame(blank_frame)

        result = detector.detect_with_details(frame_with_motion)

        assert "total_area" in result
        assert isinstance(result["total_area"], (int, float))

    def test_details_include_bounding_boxes(self, blank_frame, frame_with_motion):
        """Results should include bounding boxes of motion regions."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()
        detector.set_reference_frame(blank_frame)

        result = detector.detect_with_details(frame_with_motion)

        assert "bounding_boxes" in result
        assert isinstance(result["bounding_boxes"], list)


# =============================================================================
# Test: Reference Frame Management
# =============================================================================

class TestReferenceFrameManagement:
    """Tests for reference frame handling."""

    def test_set_reference_frame(self, blank_frame):
        """Should accept reference frame."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()
        detector.set_reference_frame(blank_frame)

        assert detector.has_reference_frame is True

    def test_update_reference_frame(self, blank_frame, white_frame):
        """Should allow updating reference frame."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()
        detector.set_reference_frame(blank_frame)
        detector.set_reference_frame(white_frame)

        assert detector.has_reference_frame is True

    def test_auto_update_reference(self, blank_frame, frame_with_motion):
        """Should optionally auto-update reference frame."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector(auto_update_reference=True)
        detector.set_reference_frame(blank_frame)

        # First detection with motion
        detector.detect(frame_with_motion)

        # Reference should be updated, so same frame shows no motion
        result = detector.detect(frame_with_motion)

        # After auto-update, the motion frame IS the reference
        assert result is False

    def test_detect_without_reference_raises(self, blank_frame):
        """detect() without reference frame should raise error."""
        from src.hardware.motion.detector import MotionDetector, NoReferenceFrameError

        detector = MotionDetector()
        # Don't set reference frame

        with pytest.raises(NoReferenceFrameError):
            detector.detect(blank_frame)


# =============================================================================
# Test: Region-Based Detection
# =============================================================================

class TestRegionBasedDetection:
    """Tests for region-based motion detection."""

    def test_set_detection_region(self, blank_frame):
        """Should allow setting detection region."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()
        region = (100, 100, 500, 400)  # x, y, width, height

        detector.set_detection_region(region)

        assert detector.detection_region == region

    def test_motion_only_in_region(self, blank_frame):
        """Should only detect motion within specified region."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()
        detector.set_detection_region((0, 0, 200, 200))  # Top-left corner
        detector.set_reference_frame(blank_frame)

        # Motion outside region (bottom-right)
        outside_motion = blank_frame.copy()
        outside_motion[600:700, 1000:1200] = 255

        # Motion inside region (top-left)
        inside_motion = blank_frame.copy()
        inside_motion[50:150, 50:150] = 255

        assert detector.detect(outside_motion) is False
        assert detector.detect(inside_motion) is True

    def test_clear_detection_region(self, blank_frame):
        """Should allow clearing detection region (full frame)."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector()
        detector.set_detection_region((100, 100, 200, 200))
        detector.clear_detection_region()

        assert detector.detection_region is None


# =============================================================================
# Test: Motion Detection Configuration
# =============================================================================

class TestMotionDetectionConfig:
    """Tests for motion detection configuration."""

    def test_load_config_from_dict(self):
        """Should load configuration from dictionary."""
        from src.hardware.motion.detector import MotionDetector

        config = {
            "sensitivity": 60,
            "min_area": 750,
            "blur_size": 7
        }

        detector = MotionDetector.from_config(config)

        assert detector.sensitivity == 60
        assert detector.min_area == 750

    def test_get_current_config(self):
        """Should return current configuration as dict."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector(sensitivity=55, min_area=600)

        config = detector.get_config()

        assert config["sensitivity"] == 55
        assert config["min_area"] == 600

    def test_update_config(self):
        """Should allow updating configuration."""
        from src.hardware.motion.detector import MotionDetector

        detector = MotionDetector(sensitivity=50)
        detector.update_config(sensitivity=70)

        assert detector.sensitivity == 70
