"""
Database Schema Definitions for SQLite.
Defines clean DDL queries with indexes, constraints, and WAL mode configuration.
"""

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- 1. Devices Table
CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    driver TEXT,
    rated_voltage_v REAL,
    rated_current_a REAL,
    rated_rpm REAL,
    location TEXT,
    created_at TEXT NOT NULL
);

-- 2. Sensor Readings Table (Deduplicated via UNIQUE event_id)
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    device_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    temperature_c REAL NOT NULL,
    vibration_rms_g REAL,
    current_a REAL NOT NULL,
    rpm REAL NOT NULL,
    sensor_status TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'utc')),
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_dev_ts 
    ON sensor_readings(device_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_event_id 
    ON sensor_readings(event_id);

-- 3. Fault Predictions Table (Stores Rule, ML, and Hybrid Verdicts)
CREATE TABLE IF NOT EXISTS fault_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    rule_fault TEXT,
    rule_severity TEXT,
    ml_fault TEXT,
    ml_confidence REAL,
    hybrid_fault TEXT NOT NULL,
    hybrid_severity TEXT NOT NULL,
    explanation TEXT,
    recommended_action TEXT,
    conflict_detected INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now', 'utc')),
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

CREATE INDEX IF NOT EXISTS idx_fault_predictions_dev_ts 
    ON fault_predictions(device_id, timestamp DESC);

-- 4. Fault Events Table (Tracks Fault Lifecycle & Duration)
CREATE TABLE IF NOT EXISTS fault_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    fault_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    is_active INTEGER DEFAULT 1,
    trigger_values TEXT,
    created_at TEXT DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_fault_events_active 
    ON fault_events(device_id, is_active);

-- 5. Alert History Table (Alert Queue & Operator Acknowledgment)
CREATE TABLE IF NOT EXISTS alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    acknowledged INTEGER DEFAULT 0,
    acknowledged_by TEXT,
    acknowledged_at TEXT,
    created_at TEXT DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_alert_history_ack 
    ON alert_history(device_id, acknowledged, timestamp DESC);

-- 6. Users Table (Authentication & Access Control)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'operator',
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    last_login TEXT
);

-- 7. System Events Table (Audit Log for Ingestion, Brokers & Hardware)
CREATE TABLE IF NOT EXISTS system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    component TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    created_at TEXT DEFAULT (datetime('now', 'utc'))
);
"""

