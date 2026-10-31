"""
Unit Tests for SQLite Persistence and Repository.
"""

import uuid
from datetime import datetime, timezone
import pytest
from database.repository import TelemetryRepository
from database.connection import DatabaseManager


@pytest.fixture
def test_repo(tmp_path):
    """Provides an isolated test repository in temporary folder."""
    db_file = tmp_path / "test_telemetry.db"
    manager = DatabaseManager(db_path=db_file)
    return TelemetryRepository(manager=manager)


def test_insert_and_retrieve_reading(test_repo):
    event_id = str(uuid.uuid4())
    reading = {
        "event_id": event_id,
        "device_id": "motor01",
        "timestamp": "2026-10-30T10:00:00Z",
        "source": "synthetic",
        "temperature_c": 35.5,
        "vibration_rms_g": 0.15,
        "current_a": 0.55,
        "rpm": 2150.0,
        "sensor_status": "ok",
    }
    inserted = test_repo.insert_sensor_reading(reading)
    assert inserted is True

    # Duplicate check
    inserted_dup = test_repo.insert_sensor_reading(reading)
    assert inserted_dup is False

    # Retrieve
    df = test_repo.get_recent_readings(device_id="motor01", limit=10)
    assert len(df) == 1
    assert df.iloc[0]["event_id"] == event_id
    assert df.iloc[0]["temperature_c"] == 35.5


def test_alert_lifecycle(test_repo):
    alert_id = test_repo.insert_alert(
        device_id="motor01",
        severity="CRITICAL",
        title="Motor Stall Detected",
        message="Current at 2.1A, RPM at 0.",
    )
    assert alert_id > 0

    alerts = test_repo.get_alerts(device_id="motor01", only_unacknowledged=True)
    assert len(alerts) == 1
    assert alerts.iloc[0]["acknowledged"] == 0

    # Acknowledge alert
    ok = test_repo.acknowledge_alert(alert_id, user="test_engineer")
    assert ok is True

    # Should no longer appear in unacknowledged list
    unack = test_repo.get_alerts(device_id="motor01", only_unacknowledged=True)
    assert len(unack) == 0

