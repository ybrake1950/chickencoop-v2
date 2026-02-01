"""
Base camera interface using Abstract Base Class.

Provides the BaseCamera ABC that all camera implementations must extend.
"""

from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path


class BaseCamera(ABC):
    """
    Abstract base class for all camera implementations.

    All cameras must implement capture() and record() methods.
    """

    def __init__(self, name: str = "default"):
        """Initialize camera with optional name."""
        self.name = name
        self._status = "initialized"

    @abstractmethod
    def capture(self, path: Optional[Path] = None):
        """Capture a still image.

        Args:
            path: Optional path to save image file. If None, returns image data.
        """

    @abstractmethod
    def record(self, path: Path, duration: int = 30):
        """Record video to file.

        Args:
            path: Path where video file will be saved.
            duration: Recording duration in seconds (default: 30).
        """

    @property
    def status(self) -> str:
        """Get camera status."""
        return self._status

    def get_status(self) -> str:
        """Get camera status."""
        return self._status
