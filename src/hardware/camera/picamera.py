"""
Raspberry Pi Camera Implementation

PiCamera implementation using the Picamera2 library.
"""

from pathlib import Path
from typing import Optional, Tuple
import time

from src.hardware.camera.interface import Camera

try:
    from picamera2 import Picamera2
except ImportError:
    # Allow imports even when picamera2 is not available (e.g., in tests)
    Picamera2 = None


# Custom Exceptions
class CameraNotStartedError(Exception):
    """Raised when attempting operations on a non-started camera."""
    pass


class CameraRecordingError(Exception):
    """Raised when recording operations fail."""
    pass


class CameraConfigError(Exception):
    """Raised when camera configuration is invalid."""
    pass


class PiCamera(Camera):
    """Raspberry Pi camera implementation using Picamera2."""

    def __init__(
        self,
        name: str = "picamera",
        resolution: Tuple[int, int] = (1280, 720),
        framerate: int = 24,
        rotation: int = 0
    ):
        """Initialize Pi Camera.

        Args:
            name: Identifier for this camera
            resolution: Tuple of (width, height)
            framerate: Frames per second for video recording
            rotation: Camera rotation in degrees (0, 90, 180, 270)
        """
        super().__init__(name=name)
        self.resolution = resolution
        self.framerate = framerate
        self.rotation = rotation
        self._camera = None
        self.is_started = False
        self.is_recording = False
        self._recording_encoder = None

    def start(self):
        """Initialize and start the camera."""
        if Picamera2 is None:
            raise ImportError("Picamera2 library not available")

        if not self.is_started:
            self._camera = Picamera2()
            # Configure camera with resolution
            config = self._camera.create_still_configuration(
                main={"size": self.resolution}
            )
            self._camera.configure(config)
            self._camera.start()
            self.is_started = True

    def stop(self):
        """Stop the camera and release resources."""
        if self.is_started and self._camera:
            if self.is_recording:
                self.stop_recording()
            self._camera.stop()
            self.is_started = False

    def capture(self, path: Optional[Path] = None):
        """Capture a still image.

        Args:
            path: Optional path to save image file

        Returns:
            Image as numpy array if path is None, otherwise None

        Raises:
            CameraNotStartedError: If camera not started
        """
        if not self.is_started:
            raise CameraNotStartedError("Camera must be started before capturing")

        if path:
            self._camera.capture_file(str(path))
            return None
        else:
            return self._camera.capture_array()

    def start_recording(self, path: Path):
        """Start recording video to file.

        Args:
            path: Path where video file will be saved

        Raises:
            CameraNotStartedError: If camera not started
            CameraRecordingError: If already recording
        """
        if not self.is_started:
            raise CameraNotStartedError("Camera must be started before recording")

        if self.is_recording:
            raise CameraRecordingError("Already recording")

        # Start recording
        self._camera.start_recording(str(path))
        self.is_recording = True

    def stop_recording(self):
        """Stop current video recording.

        Raises:
            CameraNotStartedError: If camera not started
        """
        if not self.is_started:
            raise CameraNotStartedError("Camera must be started")

        if self.is_recording:
            self._camera.stop_recording()
            self.is_recording = False

    def record(self, path: Path, duration: int):
        """Record video for a specific duration.

        Args:
            path: Path where video file will be saved
            duration: Recording duration in seconds
        """
        self.start_recording(path)
        time.sleep(duration)
        self.stop_recording()

    def is_available(self) -> bool:
        """Check if camera hardware is available.

        Returns:
            True if camera is accessible
        """
        if Picamera2 is None:
            return False
        # In real implementation, would check hardware availability
        return True

    def set_resolution(self, width: int, height: int):
        """Set camera resolution.

        Args:
            width: Image width in pixels
            height: Image height in pixels
        """
        self.resolution = (width, height)

    def set_framerate(self, framerate: int):
        """Set camera framerate.

        Args:
            framerate: Frames per second
        """
        self.framerate = framerate

    def set_rotation(self, rotation: int):
        """Set camera rotation.

        Args:
            rotation: Rotation in degrees (0, 90, 180, 270)

        Raises:
            CameraConfigError: If rotation value is invalid
        """
        if rotation not in [0, 90, 180, 270]:
            raise CameraConfigError(
                f"Invalid rotation {rotation}. Must be 0, 90, 180, or 270"
            )
        self.rotation = rotation

    @classmethod
    def from_config(cls, config: dict) -> "PiCamera":
        """Create PiCamera from configuration dictionary.

        Args:
            config: Dictionary with camera configuration
                - resolution: List [width, height]
                - framerate: int
                - rotation: int

        Returns:
            Configured PiCamera instance
        """
        resolution = tuple(config.get("resolution", [1280, 720]))
        framerate = config.get("framerate", 24)
        rotation = config.get("rotation", 0)
        name = config.get("name", "picamera")

        return cls(
            name=name,
            resolution=resolution,
            framerate=framerate,
            rotation=rotation
        )

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
