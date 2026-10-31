"""
Model Performance Page — Evaluation Metrics, Baseline Comparison & Explainability.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from config.settings import settings
from dashboard.components.charts import create_confusion_matrix_heatmap

st.set_page_config(page_title="Model Performance | ML Analytics", page_icon="⚡", layout="wide")

if not st.session_state.get("authenticated", False):
    st.warning("Please sign in from the main portal.")
    st.stop()

st.title("🔬 Machine Learning Model Evaluation & Explainability")
st.markdown("Rigorous benchmark evaluation of Random Forest Classifier against Baseline Decision Tree.")

# Load Metrics JSON
if not settings.ML_METRICS_PATH.exists():
    st.error("Model metrics not found. Train the model using: `python ml/train.py`")
    st.stop()

with open(settings.ML_METRICS_PATH, "r", encoding="utf-8") as f:
    metrics = json.load(f)

# Load Confusion Matrix JSON
cm_data = None
if settings.ML_CONFUSION_MATRIX_PATH.exists():
    with open(settings.ML_CONFUSION_MATRIX_PATH, "r", encoding="utf-8") as f:
        cm_data = json.load(f)

# Headline Metrics Cards
k_col1, k_col2, k_col3, k_col4 = st.columns(4)

with k_col1:
    st.metric("Primary Model", "Random Forest (100 Trees)")
with k_col2:
    st.metric("Holdout Accuracy", f"{metrics['random_forest']['accuracy']*100:.2f}%")
with k_col3:
    st.metric("Weighted F1-Score", f"{metrics['random_forest']['weighted_f1']:.4f}")
with k_col4:
    base_acc = metrics["baseline_decision_tree"]["accuracy"]
    st.metric("Baseline DT Accuracy", f"{base_acc*100:.2f}%")

st.markdown("---")

# Model Comparison Section
st.subheader("1. Baseline Decision Tree vs. Tuned Random Forest")
comp_df = pd.DataFrame([
    {
        "Algorithm": "Baseline Decision Tree (Depth=5)",
        "Accuracy": metrics["baseline_decision_tree"]["accuracy"],
        "Weighted F1": metrics["baseline_decision_tree"]["weighted_f1"],
    },
    {
        "Algorithm": "Random Forest Classifier (Ensemble)",
        "Accuracy": metrics["random_forest"]["accuracy"],
        "Weighted F1": metrics["random_forest"]["weighted_f1"],
    },
])
st.table(comp_df)

st.markdown("---")

# Confusion Matrix Heatmap
st.subheader("2. Confusion Matrix (Independent Episode Holdout Set)")
if cm_data:
    fig_cm = create_confusion_matrix_heatmap(cm_data["labels"], cm_data["matrix"])
    st.plotly_chart(fig_cm, use_container_width=True)

st.markdown("---")

# Feature Importance Bar Chart
st.subheader("3. Feature Importance & Explainability")
importances = metrics.get("feature_importances", {})
if importances:
    feat_df = pd.DataFrame({
        "Feature": list(importances.keys()),
        "Importance": list(importances.values()),
    }).sort_values(by="Importance", ascending=True)

    fig_feat = px.bar(
        feat_df,
        x="Importance",
        y="Feature",
        orientation="h",
        template="plotly_dark",
        title="Gini Impurity Feature Importance",
        color="Importance",
        color_continuous_scale="Blues",
    )
    fig_feat.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#161b22", height=420)
    st.plotly_chart(fig_feat, use_container_width=True)

st.markdown("---")

# Per-Class Classification Report Table
st.subheader("4. Per-Class Precision, Recall & F1-Score")
report = metrics.get("classification_report", {})
report_rows = []
for label, scores in report.items():
    if isinstance(scores, dict):
        report_rows.append({
            "Class Label": label,
            "Precision": round(scores.get("precision", 0.0), 4),
            "Recall": round(scores.get("recall", 0.0), 4),
            "F1-Score": round(scores.get("f1-score", 0.0), 4),
            "Support (Samples)": int(scores.get("support", 0)),
        })

if report_rows:
    st.dataframe(pd.DataFrame(report_rows), use_container_width=True)

# Limitations Disclosure Box
st.markdown("""
<div class='diagnosis-box' style='border-left-color: #d29922;'>
    <h4 style='color: #d29922; margin-top: 0;'>⚠️ Engineering Scope & Synthetic Limitations Notice</h4>
    <p style='color: #c9d1d9; font-size: 0.95rem; margin-bottom: 0;'>
        This model was trained and evaluated on physics-informed synthetic motor profiles. 
        While cross-episode validation confirms zero temporal leakage across simulation runs, 
        real-world motor installations exhibit physical non-linearities, bearing wear hysteresis, 
        and acoustic noise. Transfer calibration against physical benchmark measurements is required 
        prior to safety-critical automated actuation.
    </p>
</div>
""", unsafe_allow_html=True)

