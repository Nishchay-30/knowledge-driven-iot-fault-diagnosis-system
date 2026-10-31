"""
Machine Learning Inference Engine for Real-Time Motor Fault Diagnosis.
Performs live feature extraction, confidence scoring, and fallback handling.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import joblib
import numpy as np

from config.settings import settings
from ml.features import extract_single_reading_features

logger = logging.getLogger("ml_predict")


class FaultPredictor:
    """
    Loads trained Random Forest model and provides real-time probabilistic inference.
    """

    def __init__(self, model_path: Path = settings.ML_MODEL_PATH):
        self.model_path = Path(model_path)
        self.model = None
        self.classes: List[str] = []
        self.is_loaded = False
        self.load_model()

    def load_model(self) -> bool:
        """Attempts to load the joblib model bundle."""
        if not self.model_path.exists():
            logger.warning("ML model bundle not found at %s. Operating in rules-only fallback mode.", self.model_path)
            self.is_loaded = False
            return False
        try:
            bundle = joblib.load(self.model_path)
            self.model = bundle["model"]
            self.classes = bundle.get("classes", [])
            self.feature_names = bundle.get("feature_names", [])
            self.is_loaded = True
            logger.info("Successfully loaded ML model with %s classes.", len(self.classes))
            return True
        except Exception as exc:
            logger.error("Failed to load ML model from %s: %s", self.model_path, exc)
            self.is_loaded = False
            return False

    def predict(
        self,
        current_reading: Dict[str, Any],
        recent_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[Optional[str], float, Dict[str, float]]:
        """
        Runs inference on reading.
        Returns:
            (predicted_fault: Optional[str], confidence: float, class_probabilities: Dict[str, float])
        """
        if not self.is_loaded or self.model is None:
            return None, 0.0, {}

        try:
            import pandas as pd
            features = extract_single_reading_features(current_reading, recent_history)
            feat_df = pd.DataFrame(features, columns=self.feature_names)
            probabilities = self.model.predict_proba(feat_df)[0]
            top_idx = int(np.argmax(probabilities))
            predicted_class = self.classes[top_idx]
            confidence = float(probabilities[top_idx])
            prob_dict = {cls: float(round(prob, 4)) for cls, prob in zip(self.classes, probabilities)}

            return predicted_class, round(confidence, 4), prob_dict
        except Exception as exc:
            logger.error("Inference execution error: %s", exc)
            return None, 0.0, {}


predictor = FaultPredictor()
