"""
Overview Page — Executive Asset Health, KPIs, and Connectivity.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from config.settings import settings
from database.repository import repo
from dashboard.components.charts import create_gauge

st.set_page_config(page_title="Overview | Fault Diagnosis", page_icon="⚡", layout="wide")

if not st.session_state.get("authenticated", False):
    st.warning("Please sign in from the main portal.")
    st.stop()

st.title("🏭 Executive Asset Overview — Motor 01")
st.markdown("Live condition summary for 12V Brushed DC Feed Motor (Cell 1, Station 01).")

# Fetch latest telemetry and diagnosis from SQLite
readings_df = repo.get_recent_readings(device_id="motor01", limit=1)
diag_df = repo.get_recent_predictions(device_id="motor01", limit=1)
alerts_df = repo.get_alerts(device_id="motor01", only_unacknowledged=True, limit=5)

latest_reading = readings_df.iloc[-1].to_dict() if not readings_df.empty else None
latest_diag = diag_df.iloc[0].to_dict() if not diag_df.empty else None

# Status Header Bar
status_col1, status_col2, status_col3 = st.columns([2, 1, 1])

with status_col1:
    if latest_reading:
        ts = latest_reading["timestamp"]
        st.markdown(f"**Last Telemetry Event:** `{ts}`")
    else:
        st.info("No telemetry received yet. Ensure generator or ESP32 is running.")

with status_col2:
    mqtt_cfg = settings.get_effective_mqtt_config()
    broker_name = "HiveMQ Cloud" if mqtt_cfg["broker_type"] == "hivemq_cloud" else "Local Broker"
    st.markdown(f"**Broker:** `{broker_name}`")

with status_col3:
    mode_badge = "🟢 SIMULATION" if settings.OPERATION_MODE == "simulation" else "🔵 REAL HARDWARE"
    st.markdown(f"**Mode:** {mode_badge}")

st.markdown("---")

# KPI Metric Cards
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

temp_val = latest_reading["temperature_c"] if latest_reading else 0.0
vibe_val = latest_reading["vibration_rms_g"] if latest_reading else 0.0
curr_val = latest_reading["current_a"] if latest_reading else 0.0
rpm_val = latest_reading["rpm"] if latest_reading else 0.0

with m_col1:
    st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-label'>Motor Temperature</div>
        <div class='metric-value'>{temp_val:.1f}<span class='metric-unit'>°C</span></div>
    </div>
    """, unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-label'>Vibration RMS</div>
        <div class='metric-value'>{"N/A" if vibe_val is None else format(vibe_val, ".3f")}<span class='metric-unit'>g</span></div>
    </div>
    """, unsafe_allow_html=True)

with m_col3:
    st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-label'>Armature Current</div>
        <div class='metric-value'>{curr_val:.3f}<span class='metric-unit'>A</span></div>
    </div>
    """, unsafe_allow_html=True)

with m_col4:
    st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-label'>Rotational Speed</div>
        <div class='metric-value'>{rpm_val:.0f}<span class='metric-unit'>RPM</span></div>
    </div>
    """, unsafe_allow_html=True)

# Active Diagnostic Hypothesis Banner
st.subheader("Diagnostic Status")
if latest_diag:
    sev = latest_diag["hybrid_severity"]
    fault = latest_diag["hybrid_fault"]
    explanation = latest_diag.get("explanation", "")
    rec = latest_diag.get("recommended_action", "")

    badge_class = {
        "NORMAL": "status-normal",
        "WARNING": "status-warning",
        "CRITICAL": "status-critical",
    }.get(sev, "status-unknown")

    st.markdown(f"""
    <div class='diagnosis-box'>
        <h4><span class='status-pill {badge_class}'>{sev}</span> &nbsp; {fault}</h4>
        <p style='color: #c9d1d9; margin-top: 8px;'>{explanation}</p>
        <p style='color: #58a6ff; font-weight: 600;'>Recommended Action: {rec}</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Awaiting diagnostic inference results...")

# Gauges Section
st.subheader("Operational Envelopes")
g_col1, g_col2, g_col3, g_col4 = st.columns(4)

with g_col1:
    st.plotly_chart(create_gauge(temp_val, 0, 100, "Temperature", "°C", 60.0, 75.0), use_container_width=True)
with g_col2:
    st.plotly_chart(create_gauge(vibe_val, 0, 1.0, "Vibration", "g", 0.40, 0.70), use_container_width=True)
with g_col3:
    st.plotly_chart(create_gauge(curr_val, 0, 2.5, "Current", "A", 1.10, 1.70), use_container_width=True)
with g_col4:
    st.plotly_chart(create_gauge(rpm_val, 0, 3000, "Speed", "RPM", 1400, 200), use_container_width=True)

# Quick Unacknowledged Alerts
st.subheader("🚨 Active Unacknowledged Alerts")
if not alerts_df.empty:
    for _, alert in alerts_df.iterrows():
        st.warning(f"**[{alert['severity']}] {alert['title']}** — {alert['message']} ({alert['timestamp']})")
else:
    st.success("✅ No unacknowledged alarms. Operating within healthy tolerances.")

