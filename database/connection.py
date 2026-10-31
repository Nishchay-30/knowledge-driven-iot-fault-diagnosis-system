"""
SQLite Database Connection Factory
Manages thread-safe SQLite connections with WAL mode and row factory.
"""

import sqlite3
import threading
from pathlib import Path
from contextlib import contextmanager
from config.settings import settings


class DatabaseManager:
    """
    Thread-safe connection provider for SQLite.
    """

    def __init__(self, db_path: Path = settings.DATABASE_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a thread-local SQLite connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False,
            )
            conn.row_factory = sqlite3.Row
            # Enable WAL mode and foreign keys
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA busy_timeout = 30000;")
            self._local.conn = conn
        return self._local.conn

    @contextmanager
    def session(self):
        """Context manager yielding a transaction with automatic commit/rollback."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


db_manager = DatabaseManager()

