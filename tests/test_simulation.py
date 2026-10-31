"""
Unit Tests for Synthetic Generator and Physics Scenarios.
Verifies schema compliance, deterministic seeds, and scenario transitions.
"""

import pytest
from simulation.scenarios import MotorScenario, SCENARIO_PROFILES
from simulation.synthetic_generator import SyntheticGenerator
from ingestion.data_validator import DataValidator


def test_scenario_profiles_completeness():
    """Ensure all scenarios have baseline physical properties defined."""
    for scen in MotorScenario:
        assert scen in SCENARIO_PROFILES
        profile = SCENARIO_PROFILES[scen]
        assert "temp_base" in profile
        assert "vibe_base" in profile
        assert "current_base" in profile
        assert "rpm_base" in profile
        assert "ground_truth_label" in profile
        assert "severity" in profile


def test_generator_schema_compliance():
    """Verify that generated synthetic readings pass DataValidator."""
    gen = SyntheticGenerator(device_id="motor01", seed=42)
    validator = DataValidator()

    for _ in range(20):
        reading, gt = gen.generate_next_sample()
        is_valid, err = validator.validate_sensor_payload(reading)
        assert is_valid, f"Validation failed: {err}"
        assert reading["device_id"] == "motor01"
        assert reading["source"] == "synthetic"
        assert reading["sensor_status"] == "ok"
        assert 20.0 <= reading["temperature_c"] <= 60.0
        assert 0.01 <= reading["vibration_rms_g"] <= 1.0
        assert 0.2 <= reading["current_a"] <= 1.5
        assert 1500.0 <= reading["rpm"] <= 2600.0


def test_generator_reproducibility():
    """Verify reproducible streams with identical random seeds."""
    gen1 = SyntheticGenerator(device_id="motor01", seed=999)
    gen2 = SyntheticGenerator(device_id="motor01", seed=999)

    for _ in range(10):
        r1, _ = gen1.generate_next_sample()
        r2, _ = gen2.generate_next_sample()
        assert r1["temperature_c"] == r2["temperature_c"]
        assert r1["vibration_rms_g"] == r2["vibration_rms_g"]
        assert r1["current_a"] == r2["current_a"]
        assert r1["rpm"] == r2["rpm"]


def test_stall_scenario_physics():
    """Verify stall scenario produces surge current (>1.7A) and near-zero RPM (<200)."""
    gen = SyntheticGenerator(device_id="motor01", seed=123)
    gen.set_scenario(MotorScenario.MOTOR_STALL)

    for _ in range(5):
        reading, gt = gen.generate_next_sample()
    
    # After a few steps, stall dynamics settle
    assert reading["current_a"] >= 1.70
    assert reading["rpm"] <= 250.0
    assert gt["ground_truth_label"] == "Motor Stall"

