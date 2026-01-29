"""
Database connection and schema management for SQLite.
"""

import sqlite3
from pathlib import Path
from typing import Union, List, Dict, Any, Optional


class Database:
    """SQLite database connection manager."""

    def __init__(self, db_path: Union[str, Path]):
        """Create database connection.

        Args:
            db_path: Path to database file or ':memory:' for in-memory database.
        """
        self._db_path = str(db_path)
        self._connection: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self) -> None:
        """Establish database connection."""
        self._connection = sqlite3.connect(self._db_path)
        self._connection.row_factory = sqlite3.Row

    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._connection is not None

    @property
    def connection(self) -> sqlite3.Connection:
        """Get the underlying connection."""
        if self._connection is None:
            raise RuntimeError("Database not connected")
        return self._connection

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "Database":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def create_tables(self) -> None:
        """
        Create all required database tables.

        Creates the following tables if they don't exist:
        - users: User accounts with email and password hash
        - chickens: Chicken registry with name, breed, color
        - headcount_logs: Headcount detection logs
        - videos: Video metadata and retention info
        """
        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chickens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                breed TEXT,
                color TEXT,
                date_registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS headcount_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                count_detected INTEGER NOT NULL,
                expected_count INTEGER,
                all_present INTEGER,
                confidence REAL,
                method TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                s3_key TEXT,
                camera TEXT,
                duration INTEGER,
                size_bytes INTEGER,
                upload_date TIMESTAMP,
                retain_permanently INTEGER DEFAULT 0
            )
        """)

        self.connection.commit()

    def execute(self, query: str, params: tuple = ()) -> "sqlite3.Cursor":
        """Execute a parameterized query.

        Args:
            query: SQL query with ? placeholders.
            params: Tuple of parameter values.

        Returns:
            sqlite3.Cursor with results.
        """
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor

    def uses_parameterized_queries(self) -> bool:
        """Indicate that this database uses parameterized queries."""
        return True

    def get_table_names(self) -> List[str]:
        """
        Get list of all table names in database.

        Returns:
            List of table names as strings.
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get column information for a table.

        Args:
            table_name: Name of the table to inspect.

        Returns:
            List of column info dicts with keys: cid, name, type, notnull, default, pk.
        """
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": row[3],
                "default": row[4],
                "pk": row[5]
            })
        return columns
