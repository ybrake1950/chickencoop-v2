"""
CSV Storage for sensor data persistence.

Provides local CSV file storage with daily rotation for sensor readings.
"""

import csv
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.models.sensor import SensorReading
from src.persistence.base import BaseStorage


class CSVStorage(BaseStorage):
    """
    CSV-based storage for sensor readings with daily file rotation.

    Files are named sensor_data_YYYYMMDD.csv and stored in the base directory.
    """

    HEADER = ["timestamp", "temperature", "humidity", "coop_id"]
    FILENAME_PATTERN = "sensor_data_{date}.csv"
    DATE_FORMAT = "%Y%m%d"

    def __init__(self, base_path: Path):
        """
        Initialize CSV storage with base directory path.

        Args:
            base_path: Directory where CSV files will be stored.
        """
        self.base_path = Path(base_path)
        self._backed_up_files: set = set()

    def _get_filename_for_date(self, target_date: date) -> str:
        """Generate filename for a specific date."""
        date_str = target_date.strftime(self.DATE_FORMAT)
        return self.FILENAME_PATTERN.format(date=date_str)

    def _get_today_file(self) -> Path:
        """Get file path for today's data."""
        return self.base_path / self._get_filename_for_date(date.today())

    def _file_needs_header(self, file_path: Path) -> bool:
        """Check if file needs header row."""
        return not file_path.exists() or file_path.stat().st_size == 0

    def write_reading(
        self,
        timestamp: datetime,
        temperature: float,
        humidity: float,
        coop_id: str
    ) -> None:
        """
        Write a sensor reading to today's CSV file.

        Args:
            timestamp: When the reading was taken.
            temperature: Temperature value.
            humidity: Humidity percentage.
            coop_id: Identifier for the coop.
        """
        file_path = self._get_today_file()
        needs_header = self._file_needs_header(file_path)

        with open(file_path, "a", newline="") as f:
            writer = csv.writer(f)
            if needs_header:
                writer.writerow(self.HEADER)

            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([timestamp_str, temperature, humidity, coop_id])

    def write_reading_model(self, reading: SensorReading) -> None:
        """
        Write a SensorReading model to today's CSV file.

        Args:
            reading: SensorReading instance to write.
        """
        self.write_reading(
            timestamp=reading.timestamp,
            temperature=reading.temperature,
            humidity=reading.humidity,
            coop_id=reading.coop_id
        )

    def read_all(
        self,
        csv_file: Path,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Read all readings from a CSV file, optionally filtering by date.

        Args:
            csv_file: Path to the CSV file to read.
            start_date: Optional start date filter (inclusive).
            end_date: Optional end date filter (inclusive).

        Returns:
            List of reading dictionaries with timestamp, temperature, humidity, coop_id.
        """
        readings = []

        with open(csv_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                reading = {
                    "timestamp": row["timestamp"],
                    "temperature": float(row["temperature"]),
                    "humidity": float(row["humidity"]),
                    "coop_id": row["coop_id"]
                }

                if start_date or end_date:
                    row_date = datetime.strptime(
                        row["timestamp"], "%Y-%m-%d %H:%M:%S"
                    ).date()

                    if start_date and row_date < start_date:
                        continue
                    if end_date and row_date > end_date:
                        continue

                readings.append(reading)

        return readings

    def read_as_models(self, csv_file: Path) -> List[SensorReading]:
        """
        Read CSV file and return list of SensorReading models.

        Args:
            csv_file: Path to the CSV file to read.

        Returns:
            List of SensorReading instances.
        """
        readings = self.read_all(csv_file)
        return [
            SensorReading(
                temperature=r["temperature"],
                humidity=r["humidity"],
                coop_id=r["coop_id"],
                timestamp=datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S")
            )
            for r in readings
        ]

    def get_file_for_date(self, target_date: date) -> Path:
        """
        Get file path for a specific date.

        Args:
            target_date: Date to get file path for.

        Returns:
            Path to the CSV file for the given date.
        """
        return self.base_path / self._get_filename_for_date(target_date)

    def list_available_dates(self) -> List[date]:
        """
        List all dates that have data files.

        Returns:
            Sorted list of dates with existing data files.
        """
        dates = []
        pattern = re.compile(r"sensor_data_(\d{8})\.csv")

        for file_path in self.base_path.glob("sensor_data_*.csv"):
            match = pattern.match(file_path.name)
            if match:
                date_str = match.group(1)
                dates.append(datetime.strptime(date_str, self.DATE_FORMAT).date())

        return sorted(dates)

    def get_latest_file(self) -> Optional[Path]:
        """
        Get the most recent data file.

        Returns:
            Path to the most recent CSV file, or None if no files exist.
        """
        dates = self.list_available_dates()
        if not dates:
            return None
        return self.get_file_for_date(max(dates))

    def get_files_for_backup(self) -> List[Path]:
        """
        Get files that need to be backed up.

        Returns files that are not today's file and have not been marked as backed up.

        Returns:
            List of file paths needing backup.
        """
        today = date.today()
        backup_files = []

        for file_path in self.base_path.glob("sensor_data_*.csv"):
            if file_path in self._backed_up_files:
                continue

            pattern = re.compile(r"sensor_data_(\d{8})\.csv")
            match = pattern.match(file_path.name)
            if match:
                date_str = match.group(1)
                file_date = datetime.strptime(date_str, self.DATE_FORMAT).date()
                if file_date < today:
                    backup_files.append(file_path)

        return backup_files

    def mark_as_backed_up(self, csv_file: Path) -> None:
        """
        Mark a file as having been backed up.

        Args:
            csv_file: Path to the file that was backed up.
        """
        self._backed_up_files.add(csv_file)

    def append_reading(self, readings: Dict[str, Any], coop_id: str) -> None:
        """
        Append sensor readings from a monitor to the CSV file.

        Writes directly to base_path if it's a .csv file, otherwise uses daily rotation.
        Handles both flat readings and nested readings from SensorMonitor.read_all().

        Args:
            readings: Dictionary with sensor readings (temperature, humidity, etc.)
            coop_id: Identifier for the coop.
        """
        timestamp = datetime.now(timezone.utc)

        # Handle nested readings from SensorMonitor (e.g., {"combined": {"temperature": 72.5}})
        temperature = readings.get("temperature")
        humidity = readings.get("humidity")

        if temperature is None or humidity is None:
            # Try to extract from nested sensor readings
            for key, value in readings.items():
                if isinstance(value, dict):
                    if temperature is None:
                        temperature = value.get("temperature")
                    if humidity is None:
                        humidity = value.get("humidity")

        temperature = temperature if temperature is not None else 0.0
        humidity = humidity if humidity is not None else 0.0

        # If base_path is a .csv file, write directly to it
        if str(self.base_path).endswith(".csv"):
            file_path = self.base_path
            needs_header = self._file_needs_header(file_path)

            with open(file_path, "a", newline="") as f:
                writer = csv.writer(f)
                if needs_header:
                    writer.writerow(self.HEADER)
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([timestamp_str, temperature, humidity, coop_id])
        else:
            self.write_reading(
                timestamp=timestamp,
                temperature=temperature,
                humidity=humidity,
                coop_id=coop_id
            )

    def save(self, data: Any) -> None:
        """Save data to CSV storage.

        Args:
            data: SensorReading instance or dict with reading data.
        """
        if isinstance(data, SensorReading):
            self.write_reading_model(data)
        elif isinstance(data, dict):
            self.append_reading(data, data.get("coop_id", "default"))

    def load(self, identifier: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load data from CSV storage.

        Args:
            identifier: Optional date string (YYYYMMDD) to load specific file.

        Returns:
            List of reading dictionaries.
        """
        if identifier:
            target_date = datetime.strptime(identifier, self.DATE_FORMAT).date()
            file_path = self.get_file_for_date(target_date)
        else:
            file_path = self.get_latest_file()

        if file_path and file_path.exists():
            return self.read_all(file_path)
        return []
