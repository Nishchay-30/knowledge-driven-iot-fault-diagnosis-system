"""
Synthetic Dataset Generator for Machine Learning Fault Classification.
Generates balanced, non-leaking simulated runs for all diagnostic classes.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from config.settings import settings
from simulation.scenarios import MotorScenario
from simulation.synthetic_generator import SyntheticGenerator


def generate_training_dataset(
    samples_per_scenario: int = 500,
    seed: int = 100,
    output_path: Path = settings.SYNTHETIC_DIR / "motor_training_data.csv",
) -> pd.DataFrame:
    """
    Simulates multi-run episodes across all scenarios and saves to CSV.
    Uses independent runs so train/test split can cleanly separate episodes.
    """
    scenarios_to_sample = [
        MotorScenario.NORMAL,
        MotorScenario.MECHANICAL_OVERLOAD,
        MotorScenario.EXCESSIVE_VIBRATION,
        MotorScenario.MOTOR_OVERHEATING,
        MotorScenario.MOTOR_SLOWDOWN,
        MotorScenario.MOTOR_STALL,
        MotorScenario.SENSOR_ERROR,
    ]

    all_rows = []
    run_counter = 0

    for scenario in scenarios_to_sample:
        # Create 5 distinct episodes per scenario to enable group-based splitting
        episodes = 5
        steps_per_episode = samples_per_scenario // episodes

        for ep in range(episodes):
            run_counter += 1
            gen = SyntheticGenerator(device_id="motor01", seed=seed + run_counter * 17)
            gen.set_scenario(scenario)

            for step in range(steps_per_episode):
                sensor_reading, ground_truth = gen.generate_next_sample()
                if sensor_reading:
                    row = sensor_reading.copy()
                    row["run_id"] = run_counter
                    row["label"] = ground_truth["ground_truth_label"]
                    all_rows.append(row)

    df = pd.DataFrame(all_rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} synthetic training samples across {len(scenarios_to_sample)} classes -> {output_path}")
    print(f"Class breakdown:\n{df['label'].value_counts()}")
    return df


if __name__ == "__main__":
    generate_training_dataset()

