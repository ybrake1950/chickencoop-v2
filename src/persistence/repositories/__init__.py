"""Repository classes for database access."""

from .user import UserRepository
from .sensor import SensorRepository

__all__ = ["UserRepository", "SensorRepository"]
