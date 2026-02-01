"""
Base storage interface.

Provides the BaseStorage ABC that all storage implementations must extend.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseStorage(ABC):
    """
    Abstract base class for storage implementations.

    All storage backends must implement save() and load() methods.
    """

    @abstractmethod
    def save(self, data: Any) -> None:
        """Save data to storage.

        Args:
            data: Data to persist.
        """

    @abstractmethod
    def load(self, identifier: Optional[str] = None) -> Any:
        """Load data from storage.

        Args:
            identifier: Optional identifier to load specific data.

        Returns:
            The loaded data.
        """
