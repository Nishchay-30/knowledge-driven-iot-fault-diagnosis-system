"""
Live Monitoring Page — Real-Time Telemetry Streaming & Scenario Controls.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
from config.settings import settings
from database.repository import repo
from simulation.scenarios import MotorScenario
from ingestion.mqtt_client import ManagedMQTTClient
from dashboard.components.charts import create_live_telemetry_chart

st.set_page_config(page_title="Live Monitoring | Fault Diagnosis", page_icon="⚡", layout="wide")

if not st.session_state.get("authenticated", False):
    st.warning("Please sign in from the main portal.")
    st.stop()

st.title("📈 Live Telemetry Monitoring — Motor 01")

# Scenario Injection Toolbar
with st.expander("🎮 Simulation Scenario & Fault Injection Controls", expanded=True):
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 1, 1])

    with ctrl_col1:
        selected_scenario = st.selectbox(
            "Inject Fault Scenario into Simulation:",
            options=[s.value for s in MotorScenario],
            format_func=lambda x: f"{x.replace('_', ' ').title()}",
            key="selected_scenario_box",
        )

    with ctrl_col2:
        st.write("")
        st.write("")
        if st.button("Apply Scenario", type="primary", use_container_width=True):
            # Publish scenario command over MQTT to iot/factory/motor01/commands
            cfg = settings.get_effective_mqtt_config()
            cmd_client = ManagedMQTTClient(f"dash_cmd_{int(time.time())}", cfg)
            if cmd_client.connect(timeout=2):
                cmd_payload = {"command": "set_scenario", "scenario": selected_scenario}
                cmd_client.publish(settings.get_commands_topic("motor01"), cmd_payload)
                cmd_client.disconnect()
                st.success(f"Dispatched scenario command: '{selected_scenario}'")
            else:
                st.error("Could not reach MQTT broker to send scenario command.")

    with ctrl_col3:
        st.write("")
        st.write("")
        auto_refresh = st.checkbox("Auto-Refresh (1s)", value=True)

# Fetch latest 60 readings from SQLite
readings_df = repo.get_recent_readings(device_id="motor01", limit=60)

if readings_df.empty:
    st.info("No live telemetry points stored yet. Run the publisher: `python simulation/mqtt_publisher.py`")
else:
    latest = readings_df.iloc[-1]
    
    # Check freshness (offline indicator)
    try:
        last_dt = pd.to_datetime(latest["timestamp"])
        now_dt = pd.Timestamp.now(tz="UTC")
        age_seconds = (now_dt - last_dt).total_seconds()
        is_stale = age_seconds > 10.0
    except Exception:
        is_stale = False

    if is_stale:
        st.error(f"⚠️ Telemetry Link Stale / Node Offline! (No reading received for {age_seconds:.0f}s)")
    else:
        st.success(f"🟢 Telemetry Stream Active (Latency: <1s | Last: {latest['timestamp']})")

    # Render synchronized 4-row live time-series chart
    fig = create_live_telemetry_chart(readings_df)
    st.plotly_chart(fig, use_container_width=True)

    # Telemetry Data Table
    with st.expander("View Raw Telemetry Log (Last 15 Frames)"):
        st.dataframe(
            readings_df.tail(15)[["timestamp", "temperature_c", "vibration_rms_g", "current_a", "rpm", "sensor_status", "event_id"]],
            use_container_width=True,
        )

# Auto-refresh loop
if auto_refresh:
    time.sleep(1.0)
    st.rerun()

