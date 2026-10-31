"""
Synthetic Sensor Data Generator for Industrial 12V DC Motor
Generates physically realistic telemetry with continuous drift, noise, and fault dynamics.
"""

import uuid
import random
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from simulation.scenarios import MotorScenario, SCENARIO_PROFILES


class SyntheticGenerator:
    """
    Simulates physical dynamics of a 12V brushed DC motor under nominal and fault modes.
    Ensures temporal continuity (thermal inertia, rotational momentum).
    """

    def __init__(self, device_id: str = "motor01", seed: Optional[int] = None):
        self.device_id = device_id
        self.seed = seed
        self.rng = random.Random(seed)
        self.current_scenario = MotorScenario.NORMAL
        self.step_count = 0
        
        # State tracking for continuous physical inertia
        profile = SCENARIO_PROFILES[self.current_scenario]
        self._temp = profile["temp_base"]
        self._rpm = profile["rpm_base"]
        self._current = profile["current_base"]
        self._vibe = profile["vibe_base"]

    def set_scenario(self, scenario: MotorScenario) -> None:
        """Dynamically switch the operating scenario."""
        if isinstance(scenario, str):
            scenario = MotorScenario(scenario)
        self.current_scenario = scenario
        self.step_count = 0

    def generate_next_sample(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Advances simulation by one timestep (nominally 1 second) and returns:
        (sensor_reading, ground_truth)
        """
        self.step_count += 1
        now_utc = datetime.now(timezone.utc).isoformat()
        profile = SCENARIO_PROFILES[self.current_scenario]

        if self.current_scenario == MotorScenario.DISCONNECTION:
            ground_truth = {
                "event_id": str(uuid.uuid4()),
                "device_id": self.device_id,
                "timestamp": now_utc,
                "scenario": self.current_scenario.value,
                "ground_truth_label": profile["ground_truth_label"],
                "severity": profile["severity"],
                "is_disconnected": True,
            }
            # Disconnection emits no sensor telemetry to MQTT
            return {}, ground_truth

        if self.current_scenario == MotorScenario.SENSOR_ERROR:
            # Inject erratic glitch or null/extreme reading
            err_type = self.rng.choice(["negative_temp", "adc_spike", "hall_glitch", "status_flag"])
            temp = -99.9 if err_type == "negative_temp" else round(self.rng.gauss(38.0, 1.0), 2)
            vibe = round(self.rng.uniform(12.0, 18.0), 3) if err_type == "adc_spike" else round(self.rng.gauss(0.15, 0.05), 3)
            current = -2.5 if err_type == "adc_spike" else round(self.rng.gauss(0.6, 0.05), 3)
            rpm = 9999.0 if err_type == "hall_glitch" else round(self.rng.gauss(2100.0, 20.0), 1)
            sensor_status = "error"
        else:
            sensor_status = profile["sensor_status"]
            # Smooth inertia tracking towards target profile
            target_temp = profile["temp_base"] + (self.step_count * profile["temp_drift"])
            target_rpm = profile["rpm_base"]
            target_current = profile["current_base"]
            target_vibe = profile["vibe_base"]

            # Physical time constants:
            # - Stall: electrical time constant is near-instantaneous (0.85 alpha)
            # - Normal/thermal: gradual damping (0.15 - 0.35 alpha)
            alpha_curr = 0.85 if self.current_scenario == MotorScenario.MOTOR_STALL else 0.30
            alpha_rpm = 0.80 if self.current_scenario == MotorScenario.MOTOR_STALL else 0.35

            self._temp += 0.15 * (target_temp - self._temp) + self.rng.gauss(0, profile["temp_std"] * 0.2)
            self._rpm += alpha_rpm * (target_rpm - self._rpm) + self.rng.gauss(0, profile["rpm_std"] * 0.3)
            self._current += alpha_curr * (target_current - self._current) + self.rng.gauss(0, profile["current_std"] * 0.25)
            self._vibe += 0.25 * (target_vibe - self._vibe) + self.rng.gauss(0, profile["vibe_std"] * 0.2)

            # Prevent unphysical negative values in nominal/overload modes
            temp = round(max(0.0, self._temp), 2)
            vibe = round(max(0.01, self._vibe), 3)
            current = round(max(0.0, self._current), 3)
            rpm = round(max(0.0, self._rpm), 1)

        event_id = str(uuid.uuid4())

        # Normalized sensor reading payload (Section 2 specification)
        sensor_reading = {
            "event_id": event_id,
            "device_id": self.device_id,
            "timestamp": now_utc,
            "source": "synthetic",
            "temperature_c": temp,
            "vibration_rms_g": vibe,
            "current_a": current,
            "rpm": rpm,
            "sensor_status": sensor_status,
        }

        # Ground truth label stored independently for validation / ML benchmarking
        ground_truth = {
            "event_id": event_id,
            "device_id": self.device_id,
            "timestamp": now_utc,
            "scenario": self.current_scenario.value,
            "ground_truth_label": profile["ground_truth_label"],
            "severity": profile["severity"],
            "is_disconnected": False,
        }

        return sensor_reading, ground_truth
