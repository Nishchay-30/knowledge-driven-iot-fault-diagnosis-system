"""
Simulation Scenarios for 12V Industrial DC Motor
Defines physics-informed sensor generation parameters for nominal and fault modes.
"""

from enum import Enum
from typing import Dict, Any


class MotorScenario(str, Enum):
    NORMAL = "normal"
    MECHANICAL_OVERLOAD = "mechanical_overload"
    EXCESSIVE_VIBRATION = "excessive_vibration"
    MOTOR_OVERHEATING = "motor_overheating"
    MOTOR_SLOWDOWN = "motor_slowdown"
    MOTOR_STALL = "motor_stall"
    SENSOR_ERROR = "sensor_error"
    DISCONNECTION = "disconnection"


# Physical parameter baselines and drift behaviors for each scenario
SCENARIO_PROFILES: Dict[MotorScenario, Dict[str, Any]] = {
    MotorScenario.NORMAL: {
        "name": "Normal Motor Operation",
        "description": "Rated 12V operation with healthy bearings, nominal mechanical load, and stable thermal dissipation.",
        "temp_base": 36.5,
        "temp_std": 0.8,
        "temp_drift": 0.01,
        "vibe_base": 0.12,
        "vibe_std": 0.02,
        "current_base": 0.58,
        "current_std": 0.03,
        "rpm_base": 2150.0,
        "rpm_std": 30.0,
        "sensor_status": "ok",
        "severity": "NORMAL",
        "ground_truth_label": "Normal",
    },
    MotorScenario.MECHANICAL_OVERLOAD: {
        "name": "Mechanical Overload",
        "description": "Excessive driven mechanical resistance or jammed conveyor causes elevated current draw and depressed speed.",
        "temp_base": 48.0,
        "temp_std": 1.2,
        "temp_drift": 0.15,
        "vibe_base": 0.28,
        "vibe_std": 0.04,
        "current_base": 1.25,
        "current_std": 0.06,
        "rpm_base": 1380.0,
        "rpm_std": 45.0,
        "sensor_status": "ok",
        "severity": "WARNING",
        "ground_truth_label": "Mechanical Overload",
    },
    MotorScenario.EXCESSIVE_VIBRATION: {
        "name": "Excessive Vibration",
        "description": "Loose base mounting bolts, structural resonance, or rotor dynamic unbalance producing high acceleration.",
        "temp_base": 40.0,
        "temp_std": 1.0,
        "temp_drift": 0.02,
        "vibe_base": 0.55,
        "vibe_std": 0.08,
        "current_base": 0.65,
        "current_std": 0.04,
        "rpm_base": 2080.0,
        "rpm_std": 40.0,
        "sensor_status": "ok",
        "severity": "WARNING",
        "ground_truth_label": "Excessive Vibration",
    },
    MotorScenario.MOTOR_OVERHEATING: {
        "name": "Motor Overheating",
        "description": "Cooling ventilation blockage or sustained thermal stress driving casing temperature above 65°C.",
        "temp_base": 68.0,
        "temp_std": 1.5,
        "temp_drift": 0.30,  # Progressive thermal accumulation
        "vibe_base": 0.22,
        "vibe_std": 0.03,
        "current_base": 1.10,
        "current_std": 0.05,
        "rpm_base": 1820.0,
        "rpm_std": 35.0,
        "sensor_status": "ok",
        "severity": "CRITICAL",
        "ground_truth_label": "Motor Overheating",
    },
    MotorScenario.MOTOR_SLOWDOWN: {
        "name": "Motor Slowdown",
        "description": "DC power rail voltage sag (e.g. dropping to 8.5V) or dry bearing friction leading to reduced RPM.",
        "temp_base": 35.0,
        "temp_std": 0.7,
        "temp_drift": 0.0,
        "vibe_base": 0.14,
        "vibe_std": 0.02,
        "current_base": 0.62,
        "current_std": 0.03,
        "rpm_base": 1220.0,
        "rpm_std": 30.0,
        "sensor_status": "ok",
        "severity": "WARNING",
        "ground_truth_label": "Motor Slowdown",
    },
    MotorScenario.MOTOR_STALL: {
        "name": "Motor Stall / Locked Rotor",
        "description": "Physical obstruction locking the motor shaft. Current surges near stall rating (2.0A) while RPM collapses.",
        "temp_base": 62.0,
        "temp_std": 2.0,
        "temp_drift": 0.50,
        "vibe_base": 0.05,  # Stalled motor doesn't rotate, low rotary vibration
        "vibe_std": 0.02,
        "current_base": 1.95,
        "current_std": 0.08,
        "rpm_base": 40.0,
        "rpm_std": 15.0,
        "sensor_status": "ok",
        "severity": "CRITICAL",
        "ground_truth_label": "Motor Stall",
    },
    MotorScenario.SENSOR_ERROR: {
        "name": "Intermittent Sensor Error",
        "description": "Loose wire, floating ADC pin, or sensor communication timeout injecting out-of-range artifacts.",
        "temp_base": -99.0,  # Impossible physical reading
        "temp_std": 0.0,
        "temp_drift": 0.0,
        "vibe_base": 15.8,
        "vibe_std": 2.0,
        "current_base": -1.5,
        "current_std": 0.2,
        "rpm_base": 8888.0,
        "rpm_std": 100.0,
        "sensor_status": "error",
        "severity": "UNKNOWN / SENSOR ERROR",
        "ground_truth_label": "Sensor Error",
    },
    MotorScenario.DISCONNECTION: {
        "name": "MQTT Disconnection / Telemetry Loss",
        "description": "Network drop or power interruption preventing telemetry publishing. Leads to stale/offline detection.",
        "temp_base": 0.0,
        "temp_std": 0.0,
        "temp_drift": 0.0,
        "vibe_base": 0.0,
        "vibe_std": 0.0,
        "current_base": 0.0,
        "current_std": 0.0,
        "rpm_base": 0.0,
        "rpm_std": 0.0,
        "sensor_status": "disconnected",
        "severity": "WARNING",
        "ground_truth_label": "Disconnection",
    },
}

