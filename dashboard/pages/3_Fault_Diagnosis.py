"""
Fault Diagnosis Page — Knowledge-Driven Rule Engine & ML Hybrid Explanations.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
from database.repository import repo
from ml.predict import predictor

st.set_page_config(page_title="Fault Diagnosis | Expert System", page_icon="⚡", layout="wide")

if not st.session_state.get("authenticated", False):
    st.warning("Please sign in from the main portal.")
    st.stop()

st.title("🧠 Knowledge-Driven Hybrid Fault Diagnosis")
st.markdown("Combines deterministic engineering physics rules with statistical Random Forest inference.")

# Retrieve latest predictions
preds_df = repo.get_recent_predictions(device_id="motor01", limit=20)

if preds_df.empty:
    st.info("No diagnostic predictions recorded yet. Telemetry will trigger automatic evaluation.")
    st.stop()

latest = preds_df.iloc[0]

# Hybrid Verdict Card
sev = latest["hybrid_severity"]
fault = latest["hybrid_fault"]
conf = float(latest.get("ml_confidence", 0.0))
conflict = bool(latest.get("conflict_detected", 0))

sev_color = {
    "NORMAL": "#3fb950",
    "WARNING": "#d29922",
    "CRITICAL": "#f85149",
}.get(sev, "#bc8cff")

st.markdown(f"""
<div style='background-color: #161b22; border-left: 6px solid {sev_color}; border-radius: 8px; padding: 20px; margin-bottom: 20px;'>
    <h2 style='margin: 0; color: #f0f6fc;'>{fault}</h2>
    <div style='margin-top: 8px;'>
        <span class='status-pill' style='background-color: {sev_color}22; color: {sev_color}; border: 1px solid {sev_color}66;'>
            SEVERITY: {sev}
        </span>
        &nbsp;&nbsp;
        <span style='color: #8b949e; font-size: 0.9rem;'>Evaluated at: <code>{latest['timestamp']}</code></span>
    </div>
    <p style='color: #c9d1d9; margin-top: 14px; font-size: 1.05rem;'>{latest.get('explanation', '')}</p>
    <div style='background-color: #0d1117; border-radius: 6px; padding: 12px; margin-top: 12px;'>
        <strong style='color: #58a6ff;'>🔧 Prescriptive Corrective Maintenance Action:</strong>
        <p style='color: #f0f6fc; margin: 4px 0 0 0;'>{latest.get('recommended_action', '')}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Diagnostic Comparison: Rules vs ML
col_rule, col_ml = st.columns(2)

with col_rule:
    st.markdown("### 📋 Physics Rule-Based Expert System")
    st.markdown(f"**Suspected Condition:** `{latest['rule_fault']}`")
    st.markdown(f"**Rule Severity:** `{latest['rule_severity']}`")
    st.info(f"**Primary Rule Applied:** Knowledge Base Physics Definition")

with col_ml:
    st.markdown("### 🤖 Random Forest Classifier")

    ml_fault = latest.get("ml_fault")

    ml_available = (
        ml_fault is not None
        and str(ml_fault).strip().lower()
        not in ("", "none", "nan", "null")
    )

    if not ml_available:
        st.markdown("**Predicted Class:** `Not Evaluated`")
        st.markdown("**Statistical Confidence:** `N/A`")

        st.info(
            "ML diagnosis unavailable for real ESP32 data. "
            "The vibration sensor is disconnected. "
            "Rule-based diagnosis is active."
        )

        st.caption("Consensus: Not Applicable")

    else:
        st.markdown(f"**Predicted Class:** `{ml_fault}`")
        st.markdown(
            f"**Statistical Confidence:** `{conf*100:.1f}%`"
        )

        st.progress(min(1.0, max(0.0, conf)))

        if conflict:
            st.warning(
                "Diagnostic Conflict: Rule and ML "
                "predictions disagree."
            )
        else:
            st.success(
                "Rule-based and ML predictions agree."
            )


st.markdown("---")

# Historical Diagnoses Table
st.subheader("📜 Recent Diagnostic Audit Trail")
display_cols = [
    "timestamp",
    "hybrid_fault",
    "hybrid_severity",
    "rule_fault",
    "ml_fault",
    "ml_confidence",
    "conflict_detected",
]
st.dataframe(preds_df[display_cols], use_container_width=True)

