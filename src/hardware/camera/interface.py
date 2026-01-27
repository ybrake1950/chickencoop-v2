"""
Camera Hardware Interface

Base abstraction layer for camera hardware implementations.
"""

from typing import Optional
from pathlib import Path


class Camera:
    """Base camera interface that all camera implementations must follow."""

    def __init__(self, name: str = "default"):
        """Initialize camera with optional name.

        Args:
            name: Identifier for this camera instance
        """
        self.name = name

    def capture(self, path: Optional[Path] = None):
        """Capture a still image.

        Args:
            path: Optional path to save image file. If None, returns image array.

        Returns:
            Image as numpy array if path is None, otherwise None
        """
        raise NotImplementedError("Subclasses must implement capture()")

    def start_recording(self, path: Path):
        """Start recording video to file.

        Args:
            path: Path where video file will be saved
        """
        raise NotImplementedError("Subclasses must implement start_recording()")

    def stop_recording(self):
        """Stop current video recording."""
        raise NotImplementedError("Subclasses must implement stop_recording()")

    def is_available(self) -> bool:
        """Check if camera hardware is available.

        Returns:
            True if camera is accessible, False otherwise
        """
        raise NotImplementedError("Subclasses must implement is_available()")
