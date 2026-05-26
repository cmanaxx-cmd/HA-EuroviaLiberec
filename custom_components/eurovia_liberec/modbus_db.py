"""SQLite database for storing Modbus measurements."""
import logging
import sqlite3
from datetime import datetime
from typing import List, Optional

_LOGGER = logging.getLogger(__name__)


class ModbusDatabase:
    """SQLite database manager for Modbus data."""

    def __init__(self, db_path: str = "/config/eurovia_db.sqlite"):
        """Initialize database."""
        self.db_path = db_path
        self.conn = None

    def init_db(self) -> None:
        """Initialize database and create tables."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()

            # Create measurements table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    temp_rad1 REAL,
                    temp_rad2 REAL,
                    temp_rad3 REAL,
                    temp_aku1h REAL,
                    temp_aku1s REAL,
                    temp_aku2h REAL,
                    temp_aku2s REAL,
                    temp_tc1 REAL,
                    temp_tc2 REAL,
                    other_10 INTEGER,
                    other_11 INTEGER,
                    other_12 INTEGER,
                    other_13 INTEGER,
                    other_14 INTEGER,
                    other_15 INTEGER,
                    other_16 INTEGER,
                    other_17 INTEGER,
                    other_18 INTEGER,
                    other_19 INTEGER,
                    other_20 INTEGER,
                    other_21 INTEGER,
                    other_22 INTEGER,
                    other_23 INTEGER,
                    other_24 INTEGER,
                    other_25 INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Create index on timestamp
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON measurements(timestamp)"
            )

            self.conn.commit()
            _LOGGER.info(f"Database initialized: {self.db_path}")

        except Exception as e:
            _LOGGER.error(f"Database initialization error: {e}")

    def insert_measurement(
        self,
        timestamp: datetime,
        temperatures: List[float],
        others: List[int],
    ) -> bool:
        """Insert measurement into database."""
        try:
            if not self.conn:
                self.init_db()

            cursor = self.conn.cursor()

            cursor.execute(
                """
                INSERT INTO measurements (
                    timestamp,
                    temp_rad1, temp_rad2, temp_rad3,
                    temp_aku1h, temp_aku1s, temp_aku2h, temp_aku2s,
                    temp_tc1, temp_tc2,
                    other_10, other_11, other_12, other_13, other_14, other_15,
                    other_16, other_17, other_18, other_19, other_20, other_21,
                    other_22, other_23, other_24, other_25
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp.isoformat(),
                    *temperatures,
                    *others,
                ),
            )

            self.conn.commit()
            _LOGGER.debug(f"Measurement inserted: {timestamp}")
            return True

        except Exception as e:
            _LOGGER.error(f"Database insertion error: {e}")
            return False

    def get_measurements(
        self, days: int = 7, limit: int = 10000
    ) -> Optional[List]:
        """Get measurements from last N days."""
        try:
            if not self.conn:
                self.init_db()

            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT * FROM measurements
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (days, limit),
            )

            rows = cursor.fetchall()
            return rows

        except Exception as e:
            _LOGGER.error(f"Database query error: {e}")
            return None

    def get_all_measurements(self, limit: int = 10000) -> Optional[List]:
        """Get all measurements."""
        try:
            if not self.conn:
                self.init_db()

            cursor = self.conn.cursor()

            cursor.execute(
                "SELECT * FROM measurements ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )

            rows = cursor.fetchall()
            return rows

        except Exception as e:
            _LOGGER.error(f"Database query error: {e}")
            return None

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
