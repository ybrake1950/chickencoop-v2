"""
TDD Tests: Database Connection

These tests define the expected behavior for SQLite database connection.
Implement src/persistence/database.py to make these tests pass.

Run: pytest tdd/phase3_persistence/local_db/test_database_connection.py -v
"""

import pytest
from pathlib import Path


# =============================================================================
# Test: Database Connection
# =============================================================================

class TestDatabaseConnection:
    """Tests for database connection management."""

    def test_create_connection(self, test_db_path: Path):
        """Should create a database connection."""
        from src.persistence.database import Database

        db = Database(test_db_path)

        assert db.is_connected is True

    def test_connection_creates_file(self, test_db_path: Path):
        """Database file should be created."""
        from src.persistence.database import Database

        db = Database(test_db_path)

        assert test_db_path.exists()

    def test_close_connection(self, test_db_path: Path):
        """Should close connection properly."""
        from src.persistence.database import Database

        db = Database(test_db_path)
        db.close()

        assert db.is_connected is False

    def test_context_manager(self, test_db_path: Path):
        """Should support context manager."""
        from src.persistence.database import Database

        with Database(test_db_path) as db:
            assert db.is_connected is True

    def test_in_memory_database(self):
        """Should support in-memory database."""
        from src.persistence.database import Database

        db = Database(":memory:")

        assert db.is_connected is True


# =============================================================================
# Test: Schema Migration
# =============================================================================

class TestSchemaMigration:
    """Tests for database schema creation."""

    def test_create_all_tables(self, test_db_path: Path):
        """Should create all required tables."""
        from src.persistence.database import Database

        db = Database(test_db_path)
        db.create_tables()

        tables = db.get_table_names()

        assert "users" in tables
        assert "chickens" in tables
        assert "headcount_logs" in tables
        assert "videos" in tables

    def test_tables_have_correct_columns(self, test_db_path: Path):
        """Tables should have expected columns."""
        from src.persistence.database import Database

        db = Database(test_db_path)
        db.create_tables()

        user_columns = db.get_columns("users")
        column_names = [c["name"] for c in user_columns]

        assert "id" in column_names
        assert "email" in column_names
        assert "password_hash" in column_names


# =============================================================================
# Test: Repository Base
# =============================================================================

class TestUserRepository:
    """Tests for user repository."""

    def test_create_user(self, test_db_path: Path, sample_user):
        """Should create a new user."""
        from src.persistence.database import Database
        from src.persistence.repositories.user import UserRepository

        db = Database(test_db_path)
        db.create_tables()
        repo = UserRepository(db)

        user_id = repo.create(sample_user["email"], sample_user["password"])

        assert user_id is not None
        assert isinstance(user_id, int)

    def test_get_user_by_email(self, test_db_path: Path, sample_user):
        """Should retrieve user by email."""
        from src.persistence.database import Database
        from src.persistence.repositories.user import UserRepository

        db = Database(test_db_path)
        db.create_tables()
        repo = UserRepository(db)
        repo.create(sample_user["email"], sample_user["password"])

        user = repo.get_by_email(sample_user["email"])

        assert user is not None
        assert user["email"] == sample_user["email"]

    def test_user_not_found_returns_none(self, test_db_path: Path):
        """Should return None for non-existent user."""
        from src.persistence.database import Database
        from src.persistence.repositories.user import UserRepository

        db = Database(test_db_path)
        db.create_tables()
        repo = UserRepository(db)

        user = repo.get_by_email("nonexistent@example.com")

        assert user is None

    def test_verify_password(self, test_db_path: Path, sample_user):
        """Should verify correct password."""
        from src.persistence.database import Database
        from src.persistence.repositories.user import UserRepository

        db = Database(test_db_path)
        db.create_tables()
        repo = UserRepository(db)
        repo.create(sample_user["email"], sample_user["password"])

        result = repo.verify_password(sample_user["email"], sample_user["password"])

        assert result is True

    def test_wrong_password_fails(self, test_db_path: Path, sample_user):
        """Should reject wrong password."""
        from src.persistence.database import Database
        from src.persistence.repositories.user import UserRepository

        db = Database(test_db_path)
        db.create_tables()
        repo = UserRepository(db)
        repo.create(sample_user["email"], sample_user["password"])

        result = repo.verify_password(sample_user["email"], "wrong_password")

        assert result is False
