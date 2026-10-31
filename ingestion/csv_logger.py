"""
CSV Telemetry Logger Module
Thread-safe local CSV logger fulfilling Layer 1 storage requirements.
"""

import os
import csv
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd


CSV_FIELDNAMES = [
    "event_id",
    "device_id",
    "timestamp",
    "source",
    "temperature_c",
    "vibration_rms_g",
    "current_a",
    "rpm",
    "sensor_status",
]


class CSVLogger:
    """
    Safely logs incoming telemetry to a CSV file with automatic header creation and thread-safe locking.
    """

    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._ensure_header()

    def _ensure_header(self) -> None:
        with self._lock:
            if not self.filepath.exists() or self.filepath.stat().st_size == 0:
                with open(self.filepath, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
                    writer.writeheader()

    def append_reading(self, reading: Dict[str, Any]) -> bool:
        """Appends a validated reading dictionary to CSV."""
        row = {col: reading.get(col, "") for col in CSV_FIELDNAMES}
        with self._lock:
            try:
                with open(self.filepath, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
                    writer.writerow(row)
                return True
            except Exception as exc:
                print(f"Error appending reading to CSV {self.filepath}: {exc}")
                return False

    def get_recent_readings(self, limit: int = 100) -> pd.DataFrame:
        """Loads the most recent readings into a Pandas DataFrame."""
        with self._lock:
            if not self.filepath.exists() or self.filepath.stat().st_size == 0:
                return pd.DataFrame(columns=CSV_FIELDNAMES)
            try:
                df = pd.read_csv(self.filepath)
                if not df.empty and limit > 0:
                    return df.tail(limit)
                return df
            except Exception:
                return pd.DataFrame(columns=CSV_FIELDNAMES)

    def clear(self) -> None:
        """Resets the CSV file with headers only."""
        with self._lock:
            with open(self.filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
                writer.writeheader()

