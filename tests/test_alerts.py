"""
Unit Tests for Alert Persistence, Cooldown, and Recovery.
"""

import time
import pytest
from ingestion.mqtt_subscriber import TelemetryIngestionService


def test_alert_persistence_debouncing():
    service = TelemetryIngestionService(device_id="motor01")
    service.consecutive_threshold = 3
    service.alert_cooldown_sec = 10.0

    # Simulate warning scenario (Mechanical Overload)
    diag_warning = {
        "hybrid_severity": "WARNING",
        "hybrid_fault": "Mechanical Overload",
        "hybrid_confidence": 0.88,
        "recommended_action": "Reduce conveyor load",
    }
    reading = {
        "event_id": "test-alert-evt",
        "device_id": "motor01",
        "timestamp": "2026-10-30T11:00:00Z",
        "temperature_c": 45.0,
        "vibration_rms_g": 0.25,
        "current_a": 1.25,
        "rpm": 1400.0,
        "sensor_status": "ok",
    }

    # Reading 1: counter = 1 -> no alert dispatched
    service._evaluate_alerts("motor01", diag_warning, reading)
    assert service.fault_counters["motor01"] == 1
    assert "motor01" not in service.last_alert_time

    # Reading 2: counter = 2 -> no alert dispatched
    service._evaluate_alerts("motor01", diag_warning, reading)
    assert service.fault_counters["motor01"] == 2
    assert "motor01" not in service.last_alert_time

    # Reading 3: counter = 3 -> consecutive threshold met -> alert dispatched!
    service._evaluate_alerts("motor01", diag_warning, reading)
    assert service.fault_counters["motor01"] == 3
    assert "motor01" in service.last_alert_time

    # Immediate Reading 4: within cooldown window -> suppressed!
    t_alert = service.last_alert_time["motor01"]
    service._evaluate_alerts("motor01", diag_warning, reading)
    assert service.last_alert_time["motor01"] == t_alert  # alert time unchanged (suppressed)

    # Recovery reading (NORMAL) -> resets fault counter to 0
    diag_normal = {"hybrid_severity": "NORMAL", "hybrid_fault": "Normal"}
    service._evaluate_alerts("motor01", diag_normal, reading)
    assert service.fault_counters["motor01"] == 0

