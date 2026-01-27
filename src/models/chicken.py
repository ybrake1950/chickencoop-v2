"""
Chicken Registry Models

Models for tracking chickens and headcount logs in the coop.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List


# =============================================================================
# Exceptions
# =============================================================================

class ValidationError(Exception):
    """Raised when model validation fails."""
    pass


# =============================================================================
# Chicken Model
# =============================================================================

class Chicken:
    """Model representing a chicken in the registry."""

    _unique_fields = ['name']

    def __init__(
        self,
        name: str,
        breed: str,
        color: Optional[str] = None,
        is_active: bool = True,
        date_registered: Optional[datetime] = None,
        color_profile: Optional[Dict[str, Any]] = None,
        size_profile: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ):
        self.name = name
        self.breed = breed
        self.color = color
        self.is_active = is_active
        self.date_registered = date_registered or datetime.now(timezone.utc)
        self.color_profile = color_profile
        self.size_profile = size_profile
        self.notes = notes

    def deactivate(self):
        """Mark chicken as inactive."""
        self.is_active = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert chicken to dictionary."""
        return {
            "name": self.name,
            "breed": self.breed,
            "color": self.color,
            "is_active": self.is_active,
            "date_registered": self.date_registered.isoformat() if self.date_registered else None,
            "color_profile": self.color_profile,
            "size_profile": self.size_profile,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chicken':
        """Create Chicken instance from dictionary."""
        date_registered = data.get('date_registered')
        if date_registered and isinstance(date_registered, str):
            date_registered = datetime.fromisoformat(date_registered)

        return cls(
            name=data['name'],
            breed=data['breed'],
            color=data.get('color'),
            is_active=data.get('is_active', True),
            date_registered=date_registered,
            color_profile=data.get('color_profile'),
            size_profile=data.get('size_profile'),
            notes=data.get('notes')
        )


# =============================================================================
# HeadcountLog Model
# =============================================================================

class HeadcountLog:
    """Model representing a headcount log entry."""

    def __init__(
        self,
        count_detected: int,
        expected_count: int,
        confidence: Optional[float] = None,
        method: Optional[str] = None,
        image_path: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.count_detected = count_detected
        self.expected_count = expected_count
        self.confidence = confidence
        self.method = method
        self.image_path = image_path
        self.timestamp = timestamp or datetime.now(timezone.utc)

    @property
    def all_present(self) -> bool:
        """Check if all chickens are present."""
        return self.count_detected == self.expected_count

    @property
    def missing_count(self) -> int:
        """Calculate number of missing chickens."""
        return max(0, self.expected_count - self.count_detected)

    def validate(self):
        """Validate the headcount log data."""
        if self.confidence is not None and (self.confidence < 0 or self.confidence > 1):
            raise ValidationError("Confidence must be between 0 and 1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert headcount log to dictionary."""
        return {
            "count_detected": self.count_detected,
            "expected_count": self.expected_count,
            "all_present": self.all_present,
            "confidence": self.confidence,
            "method": self.method,
            "image_path": self.image_path,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "missing_count": self.missing_count
        }

    def to_api_response(self) -> Dict[str, Any]:
        """Format headcount log for API response."""
        return {
            "count": self.count_detected,
            "expected": self.expected_count,
            "all_present": self.all_present,
            "confidence": self.confidence,
            "method": self.method,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HeadcountLog':
        """Create HeadcountLog instance from dictionary."""
        timestamp = data.get('timestamp')
        if timestamp and isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            count_detected=data['count_detected'],
            expected_count=data['expected_count'],
            confidence=data.get('confidence'),
            method=data.get('method'),
            image_path=data.get('image_path'),
            timestamp=timestamp
        )


# =============================================================================
# ChickenRegistry Collection
# =============================================================================

class ChickenRegistry:
    """Collection for managing multiple chickens."""

    def __init__(self, chickens: List[Chicken]):
        self.chickens = chickens

    def __len__(self) -> int:
        """Return number of chickens in registry."""
        return len(self.chickens)

    def get_active(self) -> List[Chicken]:
        """Get all active chickens."""
        return [chicken for chicken in self.chickens if chicken.is_active]

    def get_by_name(self, name: str) -> Optional[Chicken]:
        """Get chicken by name."""
        for chicken in self.chickens:
            if chicken.name == name:
                return chicken
        return None

    @property
    def expected_count(self) -> int:
        """Return count of active chickens."""
        return len(self.get_active())
