"""
Machine Learning Training Pipeline for Motor Fault Classification.
Trains Random Forest Classifier with rolling physics features, evaluates metrics,
and saves the trained model bundle and explainability artifacts.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

from config.settings import settings
from ml.features import extract_batch_features, FEATURE_NAMES
from ml.generate_dataset import generate_training_dataset


def run_training_pipeline() -> dict:
    """Runs data generation, feature engineering, model training, and evaluation."""
    data_path = settings.SYNTHETIC_DIR / "motor_training_data.csv"
    if not data_path.exists():
        print("Training dataset not found. Generating new dataset...")
        df = generate_training_dataset(output_path=data_path)
    else:
        df = pd.read_csv(data_path)

    print(f"Loaded dataset: {len(df)} samples across {df['label'].nunique()} classes.")

    # Feature extraction
    X = extract_batch_features(df)
    y = df["label"].values
    groups = df["run_id"].values

    # Train / Test split: ensure 1 run per class is in test (20% holdout) and 4 runs in train (80%)
    # Strictly zero leakage across episodes while guaranteeing all 7 classes in train & test
    test_runs = []
    train_runs = []
    for cls in df["label"].unique():
        cls_runs = sorted(df[df["label"] == cls]["run_id"].unique().tolist())
        # Hold out the last run for test
        test_runs.append(cls_runs[-1])
        train_runs.extend(cls_runs[:-1])

    train_mask = df["run_id"].isin(train_runs)
    test_mask = df["run_id"].isin(test_runs)

    X_train, X_test = X[train_mask], X[test_mask]
    y_train, y_test = y[train_mask], y[test_mask]

    print(f"Train set: {len(X_train)} samples ({len(train_runs)} runs), Test set: {len(X_test)} samples ({len(test_runs)} runs).")

    # 1. Baseline Model (Decision Tree)
    baseline_clf = DecisionTreeClassifier(max_depth=5, random_state=42)
    baseline_clf.fit(X_train, y_train)
    y_pred_base = baseline_clf.predict(X_test)
    base_acc = float(accuracy_score(y_test, y_pred_base))
    base_f1 = float(f1_score(y_test, y_pred_base, average="weighted", zero_division=0))

    # 2. Primary Model (Random Forest Classifier)
    rf_clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=4,
        random_state=42,
        class_weight="balanced",
    )
    rf_clf.fit(X_train, y_train)
    y_pred_rf = rf_clf.predict(X_test)
    rf_acc = float(accuracy_score(y_test, y_pred_rf))
    rf_f1 = float(f1_score(y_test, y_pred_rf, average="weighted", zero_division=0))

    print("\n--- MODEL PERFORMANCE COMPARISON ---")
    print(f"Baseline Decision Tree -> Accuracy: {base_acc:.4f} | Weighted F1: {base_f1:.4f}")
    print(f"Random Forest Classifier -> Accuracy: {rf_acc:.4f} | Weighted F1: {rf_f1:.4f}")

    # Detailed Classification Report
    labels = sorted(list(set(y)))
    report = classification_report(y_test, y_pred_rf, labels=labels, target_names=labels, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_pred_rf, labels=labels)

    # Feature importances
    importances = dict(zip(FEATURE_NAMES, [float(x) for x in rf_clf.feature_importances_]))
    sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))

    print("\nTop Predictive Features:")
    for feat, imp in list(sorted_importances.items())[:5]:
        print(f"  - {feat}: {imp:.4f}")

    # Save Model Bundle
    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_bundle = {
        "model": rf_clf,
        "feature_names": FEATURE_NAMES,
        "classes": rf_clf.classes_.tolist(),
        "baseline_accuracy": base_acc,
        "rf_accuracy": rf_acc,
        "rf_f1": rf_f1,
    }
    joblib.dump(model_bundle, settings.ML_MODEL_PATH)
    print(f"\nSaved trained model to {settings.ML_MODEL_PATH}")

    # Save Metrics JSON
    metrics_summary = {
        "timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "algorithm": "RandomForestClassifier",
        "n_estimators": 100,
        "baseline_decision_tree": {
            "accuracy": round(base_acc, 4),
            "weighted_f1": round(base_f1, 4),
        },
        "random_forest": {
            "accuracy": round(rf_acc, 4),
            "weighted_f1": round(rf_f1, 4),
        },
        "classification_report": report,
        "feature_importances": sorted_importances,
        "classes": labels,
        "limitations_note": "Trained on synthetic physical simulation. Real DC motor deployment requires transfer calibration against physical benchmark loads."
    }
    with open(settings.ML_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    # Save Confusion Matrix JSON
    cm_payload = {
        "labels": labels,
        "matrix": cm.tolist(),
    }
    with open(settings.ML_CONFUSION_MATRIX_PATH, "w", encoding="utf-8") as f:
        json.dump(cm_payload, f, indent=2)

    return metrics_summary


if __name__ == "__main__":
    run_training_pipeline()
