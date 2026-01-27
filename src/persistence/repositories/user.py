"""
User repository for database operations.
"""

import hashlib
from typing import Optional, Dict, Any

from src.persistence.database import Database


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, db: Database):
        """Initialize with database connection."""
        self._db = db

    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def create(self, email: str, password: str) -> int:
        """Create a new user.

        Args:
            email: User email address.
            password: Plain text password (will be hashed).

        Returns:
            The new user's ID.
        """
        cursor = self._db.connection.cursor()
        password_hash = self._hash_password(password)

        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, password_hash)
        )
        self._db.connection.commit()

        return cursor.lastrowid

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address.

        Args:
            email: Email address to search for.

        Returns:
            User dict or None if not found.
        """
        cursor = self._db.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def verify_password(self, email: str, password: str) -> bool:
        """Verify a user's password.

        Args:
            email: User email address.
            password: Plain text password to verify.

        Returns:
            True if password matches, False otherwise.
        """
        user = self.get_by_email(email)
        if user is None:
            return False

        password_hash = self._hash_password(password)
        return user["password_hash"] == password_hash
