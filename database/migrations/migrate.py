"""
Database Migration Runner for SQLite.
Discovers and executes SQL migration files in chronological sequence.
"""

import sys
from pathlib import Path
import sqlite3

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import settings


def run_migrations(db_path: Path = settings.DATABASE_PATH) -> None:
    """Executes all migration scripts in order against the SQLite database."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    migrations_dir = Path(__file__).resolve().parent

    conn = sqlite3.connect(db_path)
    try:
        # Create schema migrations table if missing
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _schema_migrations (
                filename TEXT PRIMARY KEY,
                applied_at TEXT DEFAULT (datetime('now', 'utc'))
            )
        """)
        conn.commit()

        # Find all .sql migration files
        sql_files = sorted(migrations_dir.glob("*.sql"))
        print(f"Discovered {len(sql_files)} migration files in {migrations_dir}")

        for sql_file in sql_files:
            cursor = conn.execute("SELECT filename FROM _schema_migrations WHERE filename = ?", (sql_file.name,))
            if cursor.fetchone():
                continue

            print(f"Applying migration: {sql_file.name}...")
            with open(sql_file, "r", encoding="utf-8") as f:
                script = f.read()

            conn.executescript(script)
            conn.execute("INSERT INTO _schema_migrations (filename) VALUES (?)", (sql_file.name,))
            conn.commit()
            print(f"Successfully applied {sql_file.name}")

    finally:
        conn.close()


if __name__ == "__main__":
    run_migrations()
