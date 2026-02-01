"""
Base data models for Chicken Coop application.

This module provides the BaseModel class that all data models inherit from.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypeVar

T = TypeVar("T", bound="BaseModel")


class BaseModel:
    """
    Base class for all data models.

    Provides common functionality:
    - Automatic created_at timestamp
    - Serialization (to_dict, to_json)
    - Deserialization (from_dict, from_json)
    - Validation framework
    - Equality comparison
    - Copy functionality
    """

    def __init__(self, **kwargs):
        """
        Initialize base model with created_at timestamp.

        Args:
            **kwargs: Additional attributes to set
        """
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))

        # If created_at was passed as string, parse it
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(
                self.created_at.replace("Z", "+00:00")
            )

    def validate(self) -> bool:
        """
        Validate the model.

        Override in subclasses to add validation logic.

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        return True

    def validation_errors(self) -> List[str]:
        """
        Get list of validation errors.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        try:
            self.validate()
        except Exception as e:  # pylint: disable=broad-exception-caught
            errors.append(str(e))
        return errors

    @property
    def is_valid(self) -> bool:
        """Check if model is valid without raising exceptions."""
        try:
            return self.validate()
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.

        Returns:
            Dictionary representation of the model
        """
        result: Dict[str, Any] = {}
        for key, value in self.__dict__.items():
            if key.startswith("_"):
                continue
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, BaseModel):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls: type[T], data: Dict[str, Any]) -> T:
        """
        Create model from dictionary.

        Args:
            data: Dictionary with model data

        Returns:
            New model instance
        """
        return cls(**data)

    def to_json(self) -> str:
        """
        Convert model to JSON string.

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_json(cls: type[T], json_str: str) -> T:
        """
        Create model from JSON string.

        Args:
            json_str: JSON string

        Returns:
            New model instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def copy(self: T) -> T:
        """
        Create a copy of this model.

        Returns:
            New model instance with same data
        """
        return self.__class__.from_dict(self.to_dict())

    def __eq__(self, other: object) -> bool:
        """Check equality based on all attributes."""
        if other is None:
            return False
        if not isinstance(other, self.__class__):
            return False
        return self.to_dict() == other.to_dict()

    def __hash__(self) -> int:
        """Generate hash based on JSON representation."""
        return hash(self.to_json())

    def __str__(self) -> str:
        """Return readable string representation."""
        return f"{self.__class__.__name__}({self.to_dict()})"

    def __repr__(self) -> str:
        """Return debug string representation."""
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.to_dict().items())
        return f"{self.__class__.__name__}({attrs})"


class ValidationError(Exception):
    """Raised when model validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)
