"""Coverage improvement tests for src/persistence/repositories/user.py (69% -> 80%+)."""

import sqlite3
from unittest.mock import MagicMock

import pytest

from src.persistence.repositories.user import UserRepository


@pytest.fixture
def db_with_users():
    """Create an in-memory SQLite database with a users table."""
    db = MagicMock()
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password_hash TEXT,
            role TEXT DEFAULT 'user'
        )"""
    )
    db.connection = conn
    return db


class TestUserRepositoryFindById:
    def test_find_by_id_returns_user(self, db_with_users):
        repo = UserRepository(database=db_with_users)
        user_id = repo.create("test@example.com", "password123")
        result = repo.find_by_id(user_id)
        assert result is not None
        assert result["email"] == "test@example.com"

    def test_find_by_id_returns_none_for_missing(self, db_with_users):
        repo = UserRepository(database=db_with_users)
        result = repo.find_by_id(999)
        assert result is None


class TestUserRepositoryFindAll:
    def test_find_all_returns_all_users(self, db_with_users):
        repo = UserRepository(database=db_with_users)
        repo.create("a@test.com", "pass1")
        repo.create("b@test.com", "pass2")
        repo.create("c@test.com", "pass3")
        results = repo.find_all()
        assert len(results) == 3


class TestUserRepositorySave:
    def test_save_with_existing_id(self, db_with_users):
        repo = UserRepository(database=db_with_users)
        result = repo.save({"id": 42})
        assert result == 42

    def test_save_without_id_creates_user(self, db_with_users):
        repo = UserRepository(database=db_with_users)
        result = repo.save({"email": "new@test.com", "password": "pass123"})
        assert isinstance(result, int)
        assert result > 0


class TestUserRepositoryDelete:
    def test_delete_existing_user(self, db_with_users):
        repo = UserRepository(database=db_with_users)
        user_id = repo.create("test@test.com", "pass")
        assert repo.delete(user_id) is True

    def test_delete_nonexistent_returns_false(self, db_with_users):
        repo = UserRepository(database=db_with_users)
        assert repo.delete(999) is False


class TestUserRepositoryVerifyPassword:
    def test_verify_correct_password(self, db_with_users):
        repo = UserRepository(database=db_with_users)
        repo.create("test@test.com", "mypassword")
        assert repo.verify_password("test@test.com", "mypassword") is True

    def test_verify_wrong_password(self, db_with_users):
        repo = UserRepository(database=db_with_users)
        repo.create("test@test.com", "mypassword")
        assert repo.verify_password("test@test.com", "wrongpass") is False

    def test_verify_unknown_email(self, db_with_users):
        repo = UserRepository(database=db_with_users)
        assert repo.verify_password("unknown@test.com", "pass") is False


class TestUserRepositoryDbProperty:
    def test_db_property_raises_when_none(self):
        repo = UserRepository()
        with pytest.raises(AssertionError):
            _ = repo.db
