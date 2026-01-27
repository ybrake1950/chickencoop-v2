"""
TDD Tests: Path Utilities

These tests define the expected behavior for path manipulation utilities.
Implement src/utils/path_utils.py to make these tests pass.

Run: pytest tdd/phase1_foundation/utils/test_path_utils.py -v
"""

import pytest
from pathlib import Path


# =============================================================================
# Test: Project Root Resolution
# =============================================================================

class TestProjectRootResolution:
    """Tests for finding the project root directory."""

    def test_get_project_root_returns_path(self):
        """Should return a Path object."""
        from src.utils.path_utils import get_project_root

        result = get_project_root()

        assert isinstance(result, Path)

    def test_get_project_root_is_directory(self):
        """Project root should be an existing directory."""
        from src.utils.path_utils import get_project_root

        result = get_project_root()

        assert result.is_dir()

    def test_get_project_root_contains_marker_file(self):
        """Project root should contain a marker file (e.g., pyproject.toml)."""
        from src.utils.path_utils import get_project_root

        result = get_project_root()

        # Should contain at least one of these marker files
        markers = ["pyproject.toml", "setup.py", "requirements.txt", ".git"]
        assert any((result / marker).exists() for marker in markers)


# =============================================================================
# Test: Standard Directory Paths
# =============================================================================

class TestStandardDirectoryPaths:
    """Tests for getting standard project directories."""

    def test_get_config_dir_returns_path(self):
        """Should return path to config directory."""
        from src.utils.path_utils import get_config_dir

        result = get_config_dir()

        assert isinstance(result, Path)
        assert "config" in str(result)

    def test_get_data_dir_returns_path(self):
        """Should return path to data directory."""
        from src.utils.path_utils import get_data_dir

        result = get_data_dir()

        assert isinstance(result, Path)
        assert "data" in str(result)

    def test_get_logs_dir_returns_path(self):
        """Should return path to logs directory."""
        from src.utils.path_utils import get_logs_dir

        result = get_logs_dir()

        assert isinstance(result, Path)
        assert "logs" in str(result)

    def test_get_certs_dir_returns_path(self):
        """Should return path to certificates directory."""
        from src.utils.path_utils import get_certs_dir

        result = get_certs_dir()

        assert isinstance(result, Path)
        assert "certs" in str(result)


# =============================================================================
# Test: Directory Creation
# =============================================================================

class TestDirectoryCreation:
    """Tests for creating directories safely."""

    def test_ensure_dir_creates_directory(self, tmp_path: Path):
        """Should create directory if it doesn't exist."""
        from src.utils.path_utils import ensure_dir

        new_dir = tmp_path / "new_directory"
        result = ensure_dir(new_dir)

        assert result.exists()
        assert result.is_dir()

    def test_ensure_dir_returns_existing_directory(self, tmp_path: Path):
        """Should return existing directory without error."""
        from src.utils.path_utils import ensure_dir

        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        result = ensure_dir(existing_dir)

        assert result == existing_dir
        assert result.is_dir()

    def test_ensure_dir_creates_nested_directories(self, tmp_path: Path):
        """Should create nested directories."""
        from src.utils.path_utils import ensure_dir

        nested_dir = tmp_path / "level1" / "level2" / "level3"
        result = ensure_dir(nested_dir)

        assert result.exists()
        assert result.is_dir()

    def test_ensure_dir_raises_on_file_path(self, tmp_path: Path):
        """Should raise error if path is a file."""
        from src.utils.path_utils import ensure_dir

        file_path = tmp_path / "existing_file.txt"
        file_path.write_text("content")

        with pytest.raises((FileExistsError, NotADirectoryError)):
            ensure_dir(file_path)


# =============================================================================
# Test: Video Path Generation
# =============================================================================

class TestVideoPathGeneration:
    """Tests for generating video file paths."""

    def test_get_video_path_includes_date(self):
        """Video path should include date components."""
        from src.utils.path_utils import get_video_path
        from datetime import datetime

        result = get_video_path(
            camera="indoor",
            timestamp=datetime(2025, 1, 25, 14, 30, 0)
        )

        assert "2025" in str(result)
        assert "01" in str(result) or "25" in str(result)

    def test_get_video_path_includes_camera_name(self):
        """Video path should include camera name."""
        from src.utils.path_utils import get_video_path
        from datetime import datetime

        result = get_video_path(
            camera="outdoor",
            timestamp=datetime(2025, 1, 25, 14, 30, 0)
        )

        assert "outdoor" in str(result)

    def test_get_video_path_has_mp4_extension(self):
        """Video path should have .mp4 extension."""
        from src.utils.path_utils import get_video_path
        from datetime import datetime

        result = get_video_path(
            camera="indoor",
            timestamp=datetime(2025, 1, 25, 14, 30, 0)
        )

        assert result.suffix == ".mp4"

    def test_get_video_path_uses_motion_prefix(self):
        """Motion-triggered videos should have 'motion_' prefix."""
        from src.utils.path_utils import get_video_path
        from datetime import datetime

        result = get_video_path(
            camera="indoor",
            timestamp=datetime(2025, 1, 25, 14, 30, 0),
            trigger="motion"
        )

        assert "motion" in result.name.lower()


# =============================================================================
# Test: CSV Path Generation
# =============================================================================

class TestCSVPathGeneration:
    """Tests for generating CSV file paths."""

    def test_get_csv_path_includes_date(self):
        """CSV path should include date."""
        from src.utils.path_utils import get_csv_path
        from datetime import date

        result = get_csv_path(date=date(2025, 1, 25))

        assert "2025" in str(result)
        assert "01" in str(result)
        assert "25" in str(result)

    def test_get_csv_path_has_csv_extension(self):
        """CSV path should have .csv extension."""
        from src.utils.path_utils import get_csv_path
        from datetime import date

        result = get_csv_path(date=date(2025, 1, 25))

        assert result.suffix == ".csv"

    def test_get_csv_path_uses_data_dir(self):
        """CSV path should be in data/csv directory."""
        from src.utils.path_utils import get_csv_path
        from datetime import date

        result = get_csv_path(date=date(2025, 1, 25))

        assert "csv" in str(result)


# =============================================================================
# Test: S3 Key Generation
# =============================================================================

class TestS3KeyGeneration:
    """Tests for generating S3 object keys."""

    def test_get_s3_video_key_includes_coop_id(self, monkeypatch):
        """S3 key should include coop ID prefix."""
        from src.utils.path_utils import get_s3_video_key

        monkeypatch.setenv("COOP_ID", "coop1")

        result = get_s3_video_key(filename="motion_20250125.mp4")

        assert result.startswith("coop1/")

    def test_get_s3_video_key_includes_videos_prefix(self, monkeypatch):
        """S3 key should include videos/ prefix."""
        from src.utils.path_utils import get_s3_video_key

        monkeypatch.setenv("COOP_ID", "coop1")

        result = get_s3_video_key(filename="motion_20250125.mp4")

        assert "videos/" in result

    def test_get_s3_csv_key_includes_csv_prefix(self, monkeypatch):
        """S3 CSV key should include csv/ prefix."""
        from src.utils.path_utils import get_s3_csv_key

        monkeypatch.setenv("COOP_ID", "coop1")

        result = get_s3_csv_key(filename="sensor_data_20250125.csv")

        assert "csv/" in result


# =============================================================================
# Test: Safe Filename Generation
# =============================================================================

class TestSafeFilenameGeneration:
    """Tests for generating safe filenames."""

    def test_sanitize_filename_removes_special_chars(self):
        """Should remove special characters from filename."""
        from src.utils.path_utils import sanitize_filename

        result = sanitize_filename("file<>:name.txt")

        assert "<" not in result
        assert ">" not in result
        assert ":" not in result

    def test_sanitize_filename_preserves_extension(self):
        """Should preserve file extension."""
        from src.utils.path_utils import sanitize_filename

        result = sanitize_filename("my file.mp4")

        assert result.endswith(".mp4")

    def test_sanitize_filename_replaces_spaces(self):
        """Should replace spaces with underscores."""
        from src.utils.path_utils import sanitize_filename

        result = sanitize_filename("my video file.mp4")

        assert " " not in result
        assert "_" in result

    def test_sanitize_filename_handles_empty_string(self):
        """Should handle empty string gracefully."""
        from src.utils.path_utils import sanitize_filename

        result = sanitize_filename("")

        assert result == "" or result == "_"
