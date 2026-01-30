"""Factory for creating camera instances."""

from src.hardware.camera.picamera import PiCamera
from src.hardware.camera.base import BaseCamera


class MockCamera(BaseCamera):
    """Mock camera for testing environments."""

    def capture(self, path=None):
        """Capture a still image (no-op for mock)."""
        return None

    def record(self, path=None, duration=30):
        """Record video (no-op for mock)."""
        return None

    def is_available(self):
        """Check if camera is available. Always returns True for mock."""
        return True


class USBCamera(BaseCamera):
    """USB camera placeholder for future implementation."""

    def capture(self, path=None):
        """Capture a still image (not yet implemented)."""
        return None

    def record(self, path=None, duration=30):
        """Record video (not yet implemented)."""
        return None

    def is_available(self):
        """Check if USB camera is available. Returns False until implemented."""
        return False


class CameraFactory:
    """Factory for creating camera instances by type."""

    def create(self, camera_type: str, **kwargs):
        """Create a camera instance by type.

        Args:
            camera_type: Type of camera ('picamera', 'usb', 'mock').

        Returns:
            Camera instance.
        """
        if camera_type == "picamera":
            return PiCamera(**kwargs)
        elif camera_type == "usb":
            return USBCamera(name="usb", **kwargs)
        elif camera_type == "mock":
            return MockCamera(name="mock", **kwargs)
        else:
            raise ValueError(f"Unknown camera type: {camera_type}")
