"""
Unit Tests for Machine Learning Feature Extraction, Inference, and Hybrid Diagnosis.
"""

import pytest
import numpy as np
from ml.features import extract_single_reading_features, FEATURE_NAMES
from ml.predict import FaultPredictor
from diagnosis.hybrid_engine import HybridDiagnosticEngine


def test_feature_extraction():
    reading = {
        "temperature_c": 40.0,
        "vibration_rms_g": 0.20,
        "current_a": 0.80,
        "rpm": 1900.0,
    }
    history = [
        {"temperature_c": 39.5, "vibration_rms_g": 0.18, "current_a": 0.75, "rpm": 1950.0}
    ]
    feat = extract_single_reading_features(reading, history)
    assert feat.shape == (1, len(FEATURE_NAMES))
    assert feat[0, 0] == 40.0  # temperature
    assert round(feat[0, 4], 2) == 0.50  # temp_trend = 40.0 - 39.5


def test_ml_predictor_inference():
    predictor = FaultPredictor()
    assert predictor.is_loaded is True

    normal_reading = {
        "temperature_c": 36.0,
        "vibration_rms_g": 0.12,
        "current_a": 0.60,
        "rpm": 2150.0,
        "sensor_status": "ok",
    }
    pred_cls, conf, probs = predictor.predict(normal_reading)
    assert pred_cls == "Normal"
    assert conf >= 0.80
    assert "Normal" in probs


def test_hybrid_engine_consensus():
    engine = HybridDiagnosticEngine()
    reading = {
        "device_id": "motor01",
        "event_id": "evt-001",
        "timestamp": "2026-10-30T11:00:00Z",
        "temperature_c": 36.0,
        "vibration_rms_g": 0.12,
        "current_a": 0.60,
        "rpm": 2150.0,
        "sensor_status": "ok",
    }
    diag = engine.diagnose(reading)
    assert diag["hybrid_fault"] == "Normal"
    assert diag["hybrid_severity"] == "NORMAL"
    assert diag["conflict_detected"] is False
    assert diag["hybrid_confidence"] >= 0.90

