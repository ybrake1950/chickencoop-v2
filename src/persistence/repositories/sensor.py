"""
Sensor repository for database operations.
"""

from datetime import datetime, timezone
from typing import List, Optional

from src.models.sensor import SensorReading
from src.persistence.database import Database


class SensorRepository:
    """Repository for sensor reading database operations."""

    def __init__(self, db: Database = None, database: Database = None):
        """Initialize with database connection.

        Args:
            db: Database instance (alternative parameter name).
            database: Database instance.
        """
        self._db = db or database
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Ensure sensor_readings table exists."""
        cursor = self._db.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                coop_id TEXT NOT NULL
            )
        """)
        self._db.connection.commit()

    def save(self, reading: SensorReading) -> int:
        """Save a sensor reading to the database.

        Args:
            reading: SensorReading instance to save.

        Returns:
            The new reading's ID.
        """
        cursor = self._db.connection.cursor()
        cursor.execute(
            """INSERT INTO sensor_readings
               (timestamp, temperature, humidity, coop_id)
               VALUES (?, ?, ?, ?)""",
            (
                reading.timestamp.isoformat(),
                reading.temperature,
                reading.humidity,
                reading.coop_id
            )
        )
        self._db.connection.commit()
        return cursor.lastrowid

    def get_latest(self) -> Optional[SensorReading]:
        """Get the most recent sensor reading.

        Returns:
            SensorReading or None if no readings exist.
        """
        cursor = self._db.connection.cursor()
        cursor.execute(
            "SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return SensorReading(
            temperature=row["temperature"],
            humidity=row["humidity"],
            coop_id=row["coop_id"],
            timestamp=datetime.fromisoformat(row["timestamp"])
        )

    def get_range(self, start: datetime, end: datetime) -> List[SensorReading]:
        """Get sensor readings within a time range.

        Args:
            start: Start of time range (inclusive).
            end: End of time range (inclusive).

        Returns:
            List of SensorReading instances ordered by timestamp ascending.
        """
        cursor = self._db.connection.cursor()
        cursor.execute(
            "SELECT * FROM sensor_readings WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp",
            (start.isoformat(), end.isoformat())
        )
        results = []
        for row in cursor.fetchall():
            results.append(SensorReading(
                temperature=row["temperature"],
                humidity=row["humidity"],
                coop_id=row["coop_id"],
                timestamp=datetime.fromisoformat(row["timestamp"])
            ))
        return results
