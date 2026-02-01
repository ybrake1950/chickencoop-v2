"""Coverage improvement tests for src/persistence/repositories/video.py (39% -> 80%+)."""

import sqlite3
from unittest.mock import MagicMock

import pytest

from src.persistence.repositories.video import VideoRepository


@pytest.fixture
def db_with_videos():
    """Create an in-memory SQLite database with a videos table."""
    db = MagicMock()
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            s3_key TEXT,
            camera TEXT,
            duration INTEGER,
            size_bytes INTEGER,
            upload_date TEXT,
            coop_id TEXT
        )"""
    )
    db.connection = conn
    return db


class TestVideoRepositoryFindById:
    def test_find_by_id_returns_video_dict(self, db_with_videos):
        db_with_videos.connection.execute(
            "INSERT INTO videos (s3_key, camera, duration, coop_id) VALUES (?, ?, ?, ?)",
            ("videos/test.mp4", "cam1", 30, "coop1"),
        )
        db_with_videos.connection.commit()
        repo = VideoRepository(database=db_with_videos)
        result = repo.find_by_id(1)
        assert result is not None
        assert result["s3_key"] == "videos/test.mp4"

    def test_find_by_id_returns_none_for_missing(self, db_with_videos):
        repo = VideoRepository(database=db_with_videos)
        result = repo.find_by_id(999)
        assert result is None


class TestVideoRepositoryFindByCoop:
    def test_find_by_coop_returns_matching(self, db_with_videos):
        db_with_videos.connection.execute(
            "INSERT INTO videos (s3_key, camera, coop_id) VALUES (?, ?, ?)",
            ("v1.mp4", "coop1", "coop1"),
        )
        db_with_videos.connection.execute(
            "INSERT INTO videos (s3_key, camera, coop_id) VALUES (?, ?, ?)",
            ("v2.mp4", "coop2", "coop2"),
        )
        db_with_videos.connection.commit()
        repo = VideoRepository(database=db_with_videos)
        # find_by_coop queries WHERE camera = ?
        results = repo.find_by_coop("coop1")
        assert len(results) == 1
        assert results[0]["s3_key"] == "v1.mp4"

    def test_find_by_coop_returns_empty_for_unknown(self, db_with_videos):
        repo = VideoRepository(database=db_with_videos)
        results = repo.find_by_coop("unknown")
        assert results == []


class TestVideoRepositorySave:
    def test_save_inserts_and_returns_id(self, db_with_videos):
        repo = VideoRepository(database=db_with_videos)
        video_id = repo.save(
            {
                "filename": "test.mp4",
                "s3_key": "videos/test.mp4",
                "camera": "cam1",
                "duration": 30,
                "size_bytes": 1024,
                "upload_date": "2025-01-01",
            }
        )
        assert isinstance(video_id, int)
        assert video_id > 0

    def test_save_persists_data(self, db_with_videos):
        repo = VideoRepository(database=db_with_videos)
        video_id = repo.save(
            {
                "filename": "test.mp4",
                "s3_key": "videos/test.mp4",
                "camera": "cam1",
                "duration": 30,
                "size_bytes": 1024,
                "upload_date": "2025-01-01",
            }
        )
        found = repo.find_by_id(video_id)
        assert found is not None
        assert found["s3_key"] == "videos/test.mp4"
