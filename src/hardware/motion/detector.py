"""
Motion Detection Module

Implements motion detection algorithms using frame differencing.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any


class NoReferenceFrameError(Exception):
    """Raised when motion detection is attempted without a reference frame."""


class MotionDetector:
    """
    Motion detector using frame differencing algorithm.

    Attributes:
        sensitivity: Detection sensitivity (0-100)
        min_area: Minimum area threshold for motion detection
        auto_update_reference: Whether to auto-update reference frame
        detection_region: Optional detection region (x, y, width, height)
    """

    def __init__(
        self,
        sensitivity: int = 50,
        min_area: int = 500,
        auto_update_reference: bool = False,
        blur_size: int = 21,
    ):
        """
        Initialize motion detector.

        Args:
            sensitivity: Detection sensitivity (0-100), default 50
            min_area: Minimum area for motion detection, default 500
            auto_update_reference: Auto-update reference frame, default False
            blur_size: Gaussian blur kernel size, default 21
        """
        self.sensitivity = sensitivity
        self.min_area = min_area
        self.auto_update_reference = auto_update_reference
        self.blur_size = blur_size
        self._reference_frame: Optional[np.ndarray] = None
        self.detection_region: Optional[Tuple[int, int, int, int]] = None

    @property
    def has_reference_frame(self) -> bool:
        """Check if reference frame is set."""
        return self._reference_frame is not None

    def set_reference_frame(self, frame: np.ndarray) -> None:
        """
        Set reference frame for motion detection.

        Args:
            frame: Reference frame (numpy array)
        """
        # Convert to grayscale and blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self._reference_frame = cv2.GaussianBlur(
            gray, (self.blur_size, self.blur_size), 0
        )

    def set_detection_region(self, region: Tuple[int, int, int, int]) -> None:
        """
        Set detection region.

        Args:
            region: Tuple of (x, y, width, height)
        """
        self.detection_region = region

    def clear_detection_region(self) -> None:
        """Clear detection region to use full frame."""
        self.detection_region = None

    def detect(self, frame: np.ndarray) -> bool:
        """
        Detect motion in frame.

        Args:
            frame: Current frame to check for motion

        Returns:
            True if motion detected, False otherwise

        Raises:
            NoReferenceFrameError: If no reference frame is set
        """
        if not self.has_reference_frame:
            raise NoReferenceFrameError(
                "No reference frame set. Call set_reference_frame() first."
            )

        # Convert to grayscale and blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)

        # Apply detection region if set
        assert self._reference_frame is not None
        if self.detection_region:
            x, y, w, h = self.detection_region
            frame_diff = cv2.absdiff(
                self._reference_frame[y : y + h, x : x + w],
                blurred[y : y + h, x : x + w],
            )
        else:
            frame_diff = cv2.absdiff(self._reference_frame, blurred)

        # Apply threshold based on sensitivity
        # Higher sensitivity = lower threshold
        threshold_value = int(255 * (1 - self.sensitivity / 100))
        _, thresh = cv2.threshold(frame_diff, threshold_value, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Check if any contour exceeds min_area
        motion_detected = any(cv2.contourArea(c) >= self.min_area for c in contours)

        # Auto-update reference if enabled
        if self.auto_update_reference:
            self._reference_frame = blurred

        return motion_detected

    def detect_with_details(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Detect motion and return detailed results.

        Args:
            frame: Current frame to check for motion

        Returns:
            Dictionary with motion detection details:
                - motion_detected: bool
                - contour_count: int
                - total_area: float
                - bounding_boxes: List[Tuple[int, int, int, int]]
        """
        if not self.has_reference_frame:
            raise NoReferenceFrameError(
                "No reference frame set. Call set_reference_frame() first."
            )

        # Convert to grayscale and blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)

        # Apply detection region if set
        assert self._reference_frame is not None
        if self.detection_region:
            x, y, w, h = self.detection_region
            frame_diff = cv2.absdiff(
                self._reference_frame[y : y + h, x : x + w],
                blurred[y : y + h, x : x + w],
            )
            region_offset = (x, y)
        else:
            frame_diff = cv2.absdiff(self._reference_frame, blurred)
            region_offset = (0, 0)

        # Apply threshold based on sensitivity
        threshold_value = int(255 * (1 - self.sensitivity / 100))
        _, thresh = cv2.threshold(frame_diff, threshold_value, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter contours by min_area
        valid_contours = [c for c in contours if cv2.contourArea(c) >= self.min_area]

        # Calculate details
        motion_detected = len(valid_contours) > 0
        contour_count = len(valid_contours)
        total_area = sum(cv2.contourArea(c) for c in valid_contours)

        # Get bounding boxes
        bounding_boxes = []
        for contour in valid_contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Adjust for region offset
            bounding_boxes.append((x + region_offset[0], y + region_offset[1], w, h))

        # Auto-update reference if enabled
        if self.auto_update_reference:
            self._reference_frame = blurred

        return {
            "motion_detected": motion_detected,
            "contour_count": contour_count,
            "total_area": total_area,
            "bounding_boxes": bounding_boxes,
        }

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "MotionDetector":
        """
        Create MotionDetector from configuration dictionary.

        Args:
            config: Configuration dictionary

        Returns:
            MotionDetector instance
        """
        return cls(**config)

    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.

        Returns:
            Configuration dictionary
        """
        return {
            "sensitivity": self.sensitivity,
            "min_area": self.min_area,
            "auto_update_reference": self.auto_update_reference,
            "blur_size": self.blur_size,
        }

    def update_config(self, **kwargs) -> None:
        """
        Update configuration.

        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
