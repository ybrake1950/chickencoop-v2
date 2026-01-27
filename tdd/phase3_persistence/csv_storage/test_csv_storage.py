"""
TDD Tests: CSV Storage

These tests define the expected behavior for CSV file storage operations.
Implement src/persistence/csv_storage.py to make these tests pass.

Run: pytest tdd/phase3_persistence/csv_storage/test_csv_storage.py -v

FUNCTIONALITY BEING TESTED:
- Writing sensor readings to CSV files
- Reading sensor readings from CSV files
- Daily file rotation (one file per day)
- CSV header management
- Appending to existing files
- Date-based file naming

WHY THIS MATTERS:
CSV files provide local backup of sensor data. They're uploaded to S3 daily
and can be downloaded from the dashboard for analysis. Daily rotation
prevents files from growing too large.

HOW TESTS ARE EXECUTED:
1. Tests use tmp_path fixture for temporary directories
2. CSVStorage class is instantiated with temp path
3. Sensor readings are written and read back
4. File contents and structure are verified
"""

import pytest
from pathlib import Path
from datetime import datetime, date, timezone


# =============================================================================
# Test: CSV Writer
# =============================================================================

class TestCSVWriter:
    """Tests for CSV writing functionality."""

    def test_csv_storage_creates_file(self, tmp_path: Path):
        """Writing should create CSV file if it doesn't exist."""
        from src.persistence.csv_storage import CSVStorage

        storage = CSVStorage(tmp_path)
        storage.write_reading(
            timestamp=datetime.now(timezone.utc),
            temperature=72.5,
            humidity=65.0,
            coop_id="test"
        )

        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) == 1

    def test_csv_file_has_header(self, tmp_path: Path):
        """CSV file should have header row."""
        from src.persistence.csv_storage import CSVStorage

        storage = CSVStorage(tmp_path)
        storage.write_reading(
            timestamp=datetime.now(timezone.utc),
            temperature=72.5,
            humidity=65.0,
            coop_id="test"
        )

        csv_file = list(tmp_path.glob("*.csv"))[0]
        content = csv_file.read_text()
        first_line = content.split('\n')[0]

        assert "timestamp" in first_line.lower()
        assert "temperature" in first_line.lower()
        assert "humidity" in first_line.lower()

    def test_csv_appends_to_existing_file(self, tmp_path: Path):
        """Multiple writes should append to same file."""
        from src.persistence.csv_storage import CSVStorage

        storage = CSVStorage(tmp_path)

        # Write two readings
        storage.write_reading(
            timestamp=datetime.now(timezone.utc),
            temperature=72.5,
            humidity=65.0,
            coop_id="test"
        )
        storage.write_reading(
            timestamp=datetime.now(timezone.utc),
            temperature=73.0,
            humidity=64.0,
            coop_id="test"
        )

        csv_file = list(tmp_path.glob("*.csv"))[0]
        lines = csv_file.read_text().strip().split('\n')

        # Header + 2 data rows
        assert len(lines) == 3

    def test_csv_does_not_duplicate_header(self, tmp_path: Path):
        """Header should only appear once even with multiple writes."""
        from src.persistence.csv_storage import CSVStorage

        storage = CSVStorage(tmp_path)

        for _ in range(5):
            storage.write_reading(
                timestamp=datetime.now(timezone.utc),
                temperature=72.5,
                humidity=65.0,
                coop_id="test"
            )

        csv_file = list(tmp_path.glob("*.csv"))[0]
        content = csv_file.read_text()

        # Count header occurrences
        header_count = content.lower().count("timestamp,temperature")
        assert header_count == 1

    def test_csv_write_from_sensor_reading(self, tmp_path: Path, sample_sensor_reading):
        """Should accept SensorReading model directly."""
        from src.persistence.csv_storage import CSVStorage
        from src.models.sensor import SensorReading

        storage = CSVStorage(tmp_path)
        reading = SensorReading(
            temperature=sample_sensor_reading["temperature"],
            humidity=sample_sensor_reading["humidity"],
            coop_id=sample_sensor_reading["coop_id"]
        )

        storage.write_reading_model(reading)

        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) == 1


# =============================================================================
# Test: CSV Reader
# =============================================================================

class TestCSVReader:
    """Tests for CSV reading functionality."""

    def test_read_all_returns_list(self, csv_file: Path):
        """Reading CSV should return list of readings."""
        from src.persistence.csv_storage import CSVStorage

        storage = CSVStorage(csv_file.parent)
        readings = storage.read_all(csv_file)

        assert isinstance(readings, list)

    def test_read_all_parses_values(self, csv_file: Path):
        """Readings should have parsed numeric values."""
        from src.persistence.csv_storage import CSVStorage

        storage = CSVStorage(csv_file.parent)
        readings = storage.read_all(csv_file)

        if readings:
            reading = readings[0]
            assert isinstance(reading["temperature"], float)
            assert isinstance(reading["humidity"], float)

    def test_read_returns_sensor_reading_models(self, csv_file: Path):
        """Should optionally return SensorReading models."""
        from src.persistence.csv_storage import CSVStorage
        from src.models.sensor import SensorReading

        storage = CSVStorage(csv_file.parent)
        readings = storage.read_as_models(csv_file)

        if readings:
            assert isinstance(readings[0], SensorReading)

    def test_read_empty_file_returns_empty_list(self, tmp_path: Path):
        """Reading empty CSV should return empty list."""
        from src.persistence.csv_storage import CSVStorage

        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("timestamp,temperature,humidity,coop_id\n")

        storage = CSVStorage(tmp_path)
        readings = storage.read_all(empty_file)

        assert readings == []

    def test_read_with_date_filter(self, tmp_path: Path):
        """Should filter readings by date range."""
        from src.persistence.csv_storage import CSVStorage

        # Create file with multiple dates
        csv_file = tmp_path / "sensor_data.csv"
        csv_file.write_text(
            "timestamp,temperature,humidity,coop_id\n"
            "2025-01-24 14:00:00,70.0,60.0,test\n"
            "2025-01-25 14:00:00,72.0,65.0,test\n"
            "2025-01-26 14:00:00,74.0,70.0,test\n"
        )

        storage = CSVStorage(tmp_path)
        readings = storage.read_all(
            csv_file,
            start_date=date(2025, 1, 25),
            end_date=date(2025, 1, 25)
        )

        assert len(readings) == 1
        assert readings[0]["temperature"] == 72.0


# =============================================================================
# Test: Daily File Rotation
# =============================================================================

class TestDailyFileRotation:
    """Tests for daily CSV file rotation."""

    def test_filename_includes_date(self, tmp_path: Path):
        """CSV filename should include current date."""
        from src.persistence.csv_storage import CSVStorage

        storage = CSVStorage(tmp_path)
        storage.write_reading(
            timestamp=datetime.now(timezone.utc),
            temperature=72.5,
            humidity=65.0,
            coop_id="test"
        )

        csv_file = list(tmp_path.glob("*.csv"))[0]
        today = date.today().strftime("%Y%m%d")

        assert today in csv_file.name

    def test_get_file_for_date(self, tmp_path: Path):
        """Should return correct file path for specific date."""
        from src.persistence.csv_storage import CSVStorage

        storage = CSVStorage(tmp_path)
        file_path = storage.get_file_for_date(date(2025, 1, 25))

        assert "20250125" in str(file_path)

    def test_list_available_dates(self, tmp_path: Path):
        """Should list all dates with data files."""
        from src.persistence.csv_storage import CSVStorage

        # Create files for multiple dates
        (tmp_path / "sensor_data_20250124.csv").write_text("header\n")
        (tmp_path / "sensor_data_20250125.csv").write_text("header\n")
        (tmp_path / "sensor_data_20250126.csv").write_text("header\n")

        storage = CSVStorage(tmp_path)
        dates = storage.list_available_dates()

        assert len(dates) == 3

    def test_get_latest_file(self, tmp_path: Path):
        """Should return most recent data file."""
        from src.persistence.csv_storage import CSVStorage

        # Create files for multiple dates
        (tmp_path / "sensor_data_20250124.csv").write_text("header\n")
        (tmp_path / "sensor_data_20250126.csv").write_text("header\n")
        (tmp_path / "sensor_data_20250125.csv").write_text("header\n")

        storage = CSVStorage(tmp_path)
        latest = storage.get_latest_file()

        assert "20250126" in str(latest)


# =============================================================================
# Test: CSV Backup
# =============================================================================

class TestCSVBackup:
    """Tests for CSV backup functionality."""

    def test_get_files_for_backup(self, tmp_path: Path):
        """Should identify files ready for backup."""
        from src.persistence.csv_storage import CSVStorage
        from datetime import timedelta

        # Create old file (should be backed up)
        old_date = (date.today() - timedelta(days=2)).strftime("%Y%m%d")
        (tmp_path / f"sensor_data_{old_date}.csv").write_text("header\ndata\n")

        # Create today's file (should not be backed up yet)
        today = date.today().strftime("%Y%m%d")
        (tmp_path / f"sensor_data_{today}.csv").write_text("header\ndata\n")

        storage = CSVStorage(tmp_path)
        backup_files = storage.get_files_for_backup()

        # Only old files should be returned
        assert len(backup_files) == 1
        assert old_date in str(backup_files[0])

    def test_mark_file_as_backed_up(self, tmp_path: Path):
        """Should track which files have been backed up."""
        from src.persistence.csv_storage import CSVStorage

        csv_file = tmp_path / "sensor_data_20250125.csv"
        csv_file.write_text("header\ndata\n")

        storage = CSVStorage(tmp_path)
        storage.mark_as_backed_up(csv_file)

        # File should no longer appear in backup list
        backup_files = storage.get_files_for_backup()
        assert csv_file not in backup_files
