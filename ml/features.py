"""
Feature Engineering Module for Motor Fault Diagnosis.
Extracts instantaneous, rate-of-change, and rolling window statistical features.
"""

from typing import List, Dict, Any
import numpy as np
import pandas as pd


FEATURE_NAMES = [
    "temperature_c",
    "vibration_rms_g",
    "current_a",
    "rpm",
    "temp_trend",
    "vibe_trend",
    "current_delta",
    "rpm_delta",
    "power_est_w",  # V * I = 12.0 * current_a
    "current_per_rpm",  # Torque load proxy
]


def extract_single_reading_features(
    current_reading: Dict[str, Any],
    recent_history: List[Dict[str, Any]] = None,
) -> np.ndarray:
    """
    Extracts feature vector from the latest reading and an optional sliding window history (3-5 samples).
    """
    temp = float(current_reading.get("temperature_c", 35.0))
    vibe = float(current_reading.get("vibration_rms_g", 0.12))
    current = float(current_reading.get("current_a", 0.60))
    rpm = float(current_reading.get("rpm", 2100.0))

    temp_trend = 0.0
    vibe_trend = 0.0
    current_delta = 0.0
    rpm_delta = 0.0

    if recent_history and len(recent_history) >= 1:
        prev = recent_history[-1]
        prev_temp = float(prev.get("temperature_c", temp))
        prev_vibe = float(prev.get("vibration_rms_g", vibe))
        prev_curr = float(prev.get("current_a", current))
        prev_rpm = float(prev.get("rpm", rpm))

        temp_trend = temp - prev_temp
        vibe_trend = vibe - prev_vibe
        current_delta = current - prev_curr
        rpm_delta = rpm - prev_rpm

    # Engineered physical interactions
    power_est = 12.0 * current
    current_per_rpm = current / max(rpm, 10.0)

    features = [
        temp,
        vibe,
        current,
        rpm,
        temp_trend,
        vibe_trend,
        current_delta,
        rpm_delta,
        power_est,
        current_per_rpm,
    ]
    return np.array(features, dtype=np.float32).reshape(1, -1)


def extract_batch_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes features over a time-series DataFrame of readings.
    """
    features_df = pd.DataFrame()
    features_df["temperature_c"] = df["temperature_c"].astype(float)
    features_df["vibration_rms_g"] = df["vibration_rms_g"].astype(float)
    features_df["current_a"] = df["current_a"].astype(float)
    features_df["rpm"] = df["rpm"].astype(float)

    # Calculate changes independently within each simulation run.
    # Prevents data from one episode entering another episode.

    def within_run_diff(column):
        if "run_id" in df.columns:
            return (
                df.groupby("run_id", sort=False)[column]
                .diff()
                .fillna(0.0)
            )
        return df[column].diff().fillna(0.0)

    # Trends and deltas

    features_df["temp_trend"] = within_run_diff("temperature_c")
    features_df["vibe_trend"] = within_run_diff("vibration_rms_g")
    features_df["current_delta"] = within_run_diff("current_a")
    features_df["rpm_delta"] = within_run_diff("rpm")

    # Physical domain interactions
    features_df["power_est_w"] = 12.0 * features_df["current_a"]
    features_df["current_per_rpm"] = features_df["current_a"] / features_df["rpm"].clip(lower=10.0)

    return features_df[FEATURE_NAMES]
