"""
Machine Learning Evaluation Module.
Inspects saved model artifacts, evaluates performance against test data,
and produces detailed metrics, confusion matrix, and feature importance tables.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

from config.settings import settings
from ml.features import extract_batch_features, FEATURE_NAMES


def evaluate_saved_model(test_csv_path: Path = settings.SYNTHETIC_DIR / "motor_training_data.csv") -> Dict[str, Any]:
    """
    Evaluates the currently saved Random Forest model on the synthetic test partition.
    Prints professional tabular output suitable for verification and project reports.
    """
    model_path = settings.ML_MODEL_PATH
    if not model_path.exists():
        raise FileNotFoundError(f"Trained model not found at {model_path}. Run 'python ml/train.py' first.")

    bundle = joblib.load(model_path)
    model = bundle["model"]
    feature_names = bundle.get("feature_names", FEATURE_NAMES)
    classes = bundle.get("classes", [])

    print("================================================================================")
    print("                  MACHINE LEARNING MODEL EVALUATION REPORT                      ")
    print("================================================================================")
    print(f"Model Type:        {bundle.get('model_type', 'Random Forest Classifier')}")
    print(f"Model Path:        {model_path}")
    print(f"Trained Timestamp: {bundle.get('trained_at', 'N/A')}")
    print(f"Classes ({len(classes)}):     {', '.join(classes)}")
    print(f"Total Estimators:  {getattr(model, 'n_estimators', 'N/A')}")
    print("--------------------------------------------------------------------------------")

    if not test_csv_path.exists():
        print(f"Dataset not found at {test_csv_path}. Skipping dynamic test evaluation.")
        metrics_path = settings.ML_METRICS_PATH
        if metrics_path.exists():
            with open(metrics_path, "r", encoding="utf-8") as f:
                saved_metrics = json.load(f)
            print("Loaded Stored Metrics:")
            print(json.dumps(saved_metrics, indent=2))
            return saved_metrics
        return {}

    df = pd.read_csv(test_csv_path)

    # Recreate the exact test partition (holdout of the last run per class)
    test_runs = []
    for cls in df["label"].unique():
        cls_runs = sorted(df[df["label"] == cls]["run_id"].unique().tolist())
        test_runs.append(cls_runs[-1])

    test_df = df[df["run_id"].isin(test_runs)].reset_index(drop=True)
    X_test = extract_batch_features(test_df)
    y_test = test_df["label"].values

    y_pred = model.predict(X_test)
    acc = float(accuracy_score(y_test, y_pred))
    f1_weighted = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

    print(f"\nTest Dataset Size: {len(test_df)} samples across {len(test_runs)} held-out episodes")
    print(f"Overall Accuracy:  {acc * 100:.2f}%")
    print(f"Weighted F1 Score: {f1_weighted:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, digits=4, zero_division=0))

    labels_list = sorted(list(classes))
    cm = confusion_matrix(y_test, y_pred, labels=labels_list)
    cm_df = pd.DataFrame(cm, index=[f"True: {l}" for l in labels_list], columns=[f"Pred: {l}" for l in labels_list])
    print("\nConfusion Matrix:")
    print(cm_df.to_string())

    if hasattr(model, "feature_importances_"):
        importances = dict(zip(feature_names, model.feature_importances_))
        sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        print("\nFeature Importances:")
        for feat, imp in sorted_imp:
            bar = "█" * int(imp * 40)
            print(f"  {feat:<22} : {imp:6.4f} | {bar}")

    print("================================================================================")
    print("Academic Notice: Metrics evaluated on synthetic physics simulations.")
    print("Physical motor real-world accuracy requires calibration with real sensor runs.")
    print("================================================================================")

    return {
        "accuracy": acc,
        "weighted_f1": f1_weighted,
        "classes": labels_list,
        "samples_tested": len(test_df),
    }


if __name__ == "__main__":
    evaluate_saved_model()
