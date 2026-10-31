"""
SQLite Database Repository
Implements data access operations for sensor telemetry, fault events, alerts, and users.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd
from database.connection import db_manager
from database.models import SCHEMA_SQL

logger = logging.getLogger("database_repo")


class TelemetryRepository:
    """
    Authoritative database repository for all persistence needs across Layers 3-6.
    """

    def __init__(self, manager=db_manager):
        self.manager = manager
        self.init_db()

    def init_db(self) -> None:
        """Initializes database schema and default device if missing."""
        with self.manager.session() as conn:
            conn.executescript(SCHEMA_SQL)
            # Register default motor01 asset if not already present
            cursor = conn.execute("SELECT device_id FROM devices WHERE device_id = ?", ("motor01",))
            if not cursor.fetchone():
                now_utc = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    """
                    INSERT INTO devices (device_id, name, type, driver, rated_voltage_v, 
                                         rated_current_a, rated_rpm, location, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "motor01",
                        "Primary Feed Drive Motor (Station 01)",
                        "12V Brushed DC Motor",
                        "L298N Dual H-Bridge Driver",
                        12.0,
                        0.80,
                        2000.0,
                        "Machining Cell 1",
                        now_utc,
                    ),
                )
                logger.info("Registered default device 'motor01' in SQLite database.")

    def insert_sensor_reading(self, reading: Dict[str, Any]) -> bool:
        """
        Inserts a sensor reading into SQLite. Deduplicates automatically via event_id UNIQUE constraint.
        Returns True if newly inserted, False if duplicate or failed.
        """
        query = """
        INSERT OR IGNORE INTO sensor_readings 
        (event_id, device_id, timestamp, source, temperature_c, vibration_rms_g, current_a, rpm, sensor_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self.manager.session() as conn:
                cursor = conn.execute(
                    query,
                    (
                        reading["event_id"],
                        reading["device_id"],
                        reading["timestamp"],
                        reading.get("source", "synthetic"),
                        float(reading["temperature_c"]),
                        (float(reading["vibration_rms_g"]) if reading.get("vibration_rms_g") is not None else None),
                        float(reading["current_a"]),
                        float(reading["rpm"]),
                        reading.get("sensor_status", "ok"),
                    ),
                )
                return cursor.rowcount > 0
        except Exception as exc:
            logger.error("Failed to insert sensor reading %s: %s", reading.get("event_id"), exc)
            return False

    def get_recent_readings(self, device_id: str = "motor01", limit: int = 100) -> pd.DataFrame:
        """Retrieves the N most recent sensor readings for a device."""
        query = """
        SELECT id, event_id, device_id, timestamp, source, temperature_c, vibration_rms_g, current_a, rpm, sensor_status
        FROM sensor_readings
        WHERE device_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """
        with self.manager.session() as conn:
            cursor = conn.execute(query, (device_id, limit))
            rows = [dict(row) for row in cursor.fetchall()]
        if not rows:
            return pd.DataFrame(columns=[
                "id", "event_id", "device_id", "timestamp", "source",
                "temperature_c", "vibration_rms_g", "current_a", "rpm", "sensor_status"
            ])
        df = pd.DataFrame(rows)
        # Return in ascending chronological order for plotting
        return df.iloc[::-1].reset_index(drop=True)

    def get_readings_by_time_range(
        self, device_id: str, start_iso: str, end_iso: str, limit: int = 5000
    ) -> pd.DataFrame:
        """Queries readings filtered by ISO-8601 start and end timestamps."""
        query = """
        SELECT id, event_id, device_id, timestamp, source, temperature_c, vibration_rms_g, current_a, rpm, sensor_status
        FROM sensor_readings
        WHERE device_id = ? AND timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp ASC
        LIMIT ?
        """
        with self.manager.session() as conn:
            cursor = conn.execute(query, (device_id, start_iso, end_iso, limit))
            rows = [dict(row) for row in cursor.fetchall()]
        return pd.DataFrame(rows)

    def insert_fault_prediction(self, pred: Dict[str, Any]) -> int:
        """Saves a hybrid rule/ML diagnostic conclusion."""
        query = """
        INSERT INTO fault_predictions 
        (event_id, device_id, timestamp, rule_fault, rule_severity, ml_fault, 
         ml_confidence, hybrid_fault, hybrid_severity, explanation, recommended_action, conflict_detected)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.manager.session() as conn:
            cursor = conn.execute(
                query,
                (
                    pred.get("event_id", ""),
                    pred["device_id"],
                    pred["timestamp"],
                    pred.get("rule_fault"),
                    pred.get("rule_severity"),
                    pred.get("ml_fault"),
                    float(pred.get("ml_confidence", 0.0)),
                    pred["hybrid_fault"],
                    pred["hybrid_severity"],
                    pred.get("explanation", ""),
                    pred.get("recommended_action", ""),
                    1 if pred.get("conflict_detected") else 0,
                ),
            )
            return cursor.lastrowid

    def get_recent_predictions(self, device_id: str = "motor01", limit: int = 50) -> pd.DataFrame:
        """Retrieves recent fault diagnoses."""
        query = """
        SELECT id, event_id, device_id, timestamp, rule_fault, rule_severity, 
               ml_fault, ml_confidence, hybrid_fault, hybrid_severity, 
               explanation, recommended_action, conflict_detected
        FROM fault_predictions
        WHERE device_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """
        with self.manager.session() as conn:
            cursor = conn.execute(query, (device_id, limit))
            rows = [dict(row) for row in cursor.fetchall()]
        return pd.DataFrame(rows)

    def insert_alert(
        self, device_id: str, severity: str, title: str, message: str, timestamp: Optional[str] = None
    ) -> int:
        """Records a new alert."""
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        query = """
        INSERT INTO alert_history (device_id, timestamp, severity, title, message, acknowledged)
        VALUES (?, ?, ?, ?, ?, 0)
        """
        with self.manager.session() as conn:
            cursor = conn.execute(query, (device_id, ts, severity, title, message))
            return cursor.lastrowid

    def get_alerts(self, device_id: Optional[str] = None, only_unacknowledged: bool = False, limit: int = 50) -> pd.DataFrame:
        """Queries alert records."""
        conditions = []
        params: List[Any] = []
        if device_id:
            conditions.append("device_id = ?")
            params.append(device_id)
        if only_unacknowledged:
            conditions.append("acknowledged = 0")
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
        SELECT id, device_id, timestamp, severity, title, message, acknowledged, acknowledged_by, acknowledged_at
        FROM alert_history
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT ?
        """
        params.append(limit)
        with self.manager.session() as conn:
            cursor = conn.execute(query, tuple(params))
            rows = [dict(row) for row in cursor.fetchall()]
        return pd.DataFrame(rows)

    def acknowledge_alert(self, alert_id: int, user: str = "operator") -> bool:
        """Marks an alert as acknowledged."""
        now_utc = datetime.now(timezone.utc).isoformat()
        query = """
        UPDATE alert_history
        SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = ?
        WHERE id = ?
        """
        with self.manager.session() as conn:
            cursor = conn.execute(query, (user, now_utc, alert_id))
            return cursor.rowcount > 0

    def record_system_event(
        self, event_type: str, component: str, message: str, details: Optional[str] = None
    ) -> int:
        """Logs system health, broker reconnections, or operational state shifts."""
        now_utc = datetime.now(timezone.utc).isoformat()
        query = """
        INSERT INTO system_events (timestamp, event_type, component, message, details)
        VALUES (?, ?, ?, ?, ?)
        """
        with self.manager.session() as conn:
            cursor = conn.execute(query, (now_utc, event_type, component, message, details or ""))
            return cursor.lastrowid


repo = TelemetryRepository()

