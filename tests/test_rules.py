"""
Unit Tests for Knowledge-Driven Expert Rule Engine.
"""

import pytest
from diagnosis.rule_engine import RuleEngine


@pytest.fixture
def engine():
    return RuleEngine()


def test_rule_normal_operation(engine):
    reading = {
        "temperature_c": 35.0,
        "vibration_rms_g": 0.12,
        "current_a": 0.58,
        "rpm": 2150.0,
        "sensor_status": "ok",
    }
    result = engine.evaluate(reading)
    assert result["suspected_fault"] == "Normal"
    assert result["severity"] == "NORMAL"
    assert result["confidence"] >= 0.90
    assert "RULE_007_NORMAL_OPERATION" in result["activated_rules"]


def test_rule_motor_stall(engine):
    reading = {
        "temperature_c": 55.0,
        "vibration_rms_g": 0.05,
        "current_a": 1.95,
        "rpm": 50.0,
        "sensor_status": "ok",
    }
    result = engine.evaluate(reading)
    assert result["suspected_fault"] == "Motor Stall / Locked Rotor"
    assert result["severity"] == "CRITICAL"
    assert "RULE_002_MOTOR_STALL" in result["activated_rules"]


def test_rule_overheating(engine):
    reading = {
        "temperature_c": 72.0,
        "vibration_rms_g": 0.18,
        "current_a": 1.15,
        "rpm": 1850.0,
        "sensor_status": "ok",
    }
    result = engine.evaluate(reading)
    assert result["suspected_fault"] == "Motor Overheating"
    assert result["severity"] == "CRITICAL"
    assert "RULE_003_THERMAL_OVERHEATING" in result["activated_rules"]


def test_rule_mechanical_overload(engine):
    reading = {
        "temperature_c": 45.0,
        "vibration_rms_g": 0.22,
        "current_a": 1.25,
        "rpm": 1350.0,
        "sensor_status": "ok",
    }
    result = engine.evaluate(reading)
    assert result["suspected_fault"] == "Mechanical Overload"
    assert result["severity"] == "WARNING"


def test_rule_excessive_vibration(engine):
    reading = {
        "temperature_c": 38.0,
        "vibration_rms_g": 0.65,
        "current_a": 0.65,
        "rpm": 2100.0,
        "sensor_status": "ok",
    }
    result = engine.evaluate(reading)
    assert result["suspected_fault"] == "Excessive Vibration"
    assert result["severity"] == "WARNING"


def test_rule_sensor_anomaly(engine):
    reading = {
        "temperature_c": -99.0,
        "vibration_rms_g": 18.0,
        "current_a": -2.0,
        "rpm": 9999.0,
        "sensor_status": "error",
    }
    result = engine.evaluate(reading)
    assert result["suspected_fault"] == "Sensor Acquisition Fault"
    assert result["severity"] == "UNKNOWN / SENSOR ERROR"
    assert "RULE_001_SENSOR_ANOMALY" in result["activated_rules"]

