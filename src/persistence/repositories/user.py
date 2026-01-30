"""
User repository for database operations.
"""

import hashlib
from typing import Optional, Dict, Any

from src.persistence.database import Database


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, db: Database = None, database: Database = None):
        """Initialize with database connection.

        Args:
            db: Database instance (alternative parameter name).
            database: Database instance.
        """
        self._db = db or database

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

    def find_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Find a user by ID.

        Args:
            user_id: The user ID to look up.

        Returns:
            User dictionary, or None if not found.
        """
        cursor = self._db.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def find_all(self):
        """Find all users.

        Returns:
            List of user dictionaries.
        """
        cursor = self._db.connection.cursor()
        cursor.execute("SELECT * FROM users")
        return [dict(row) for row in cursor.fetchall()]

    def save(self, user_data: Dict[str, Any]) -> int:
        """Save a user record.

        If user_data contains an 'id', returns that ID. Otherwise creates a new user.

        Args:
            user_data: Dictionary with 'email' and 'password' keys.

        Returns:
            The user's ID.
        """
        if "id" in user_data:
            return user_data["id"]
        return self.create(user_data.get("email", ""), user_data.get("password", ""))

    def delete(self, user_id: int) -> bool:
        """Delete a user by ID.

        Args:
            user_id: The user ID to delete.

        Returns:
            True if a user was deleted, False if not found.
        """
        cursor = self._db.connection.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self._db.connection.commit()
        return cursor.rowcount > 0

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
