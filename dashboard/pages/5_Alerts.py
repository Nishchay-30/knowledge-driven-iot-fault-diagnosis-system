"""
Alerts Page — Active Alarms, Operator Acknowledgment, and Incident Audit Trail.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
from database.repository import repo

st.set_page_config(page_title="Alerts | Fault Diagnosis", page_icon="⚡", layout="wide")

if not st.session_state.get("authenticated", False):
    st.warning("Please sign in from the main portal.")
    st.stop()

st.title("🚨 Industrial Alarm & Event Management")
st.markdown("Manages threshold violations, multi-reading persistence checks, and operator incident responses.")

# Fetch Unacknowledged Alerts
unack_df = repo.get_alerts(device_id="motor01", only_unacknowledged=True, limit=20)

st.subheader(f"⚠️ Active Unacknowledged Queue ({len(unack_df)})")

if unack_df.empty:
    st.success("✅ All system alarms have been acknowledged or resolved. Nominal operating state.")
else:
    for idx, row in unack_df.iterrows():
        sev = row["severity"]
        alert_id = row["id"]
        
        sev_color = "#f85149" if sev == "CRITICAL" else ("#d29922" if sev == "WARNING" else "#bc8cff")

        with st.container():
            st.markdown(f"""
            <div style='background-color: #161b22; border-left: 5px solid {sev_color}; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;'>
                <div style='display: flex; justify-content: space-between;'>
                    <strong style='color: #f0f6fc; font-size: 1.1rem;'>[{sev}] {row['title']}</strong>
                    <span style='color: #8b949e; font-size: 0.85rem;'>{row['timestamp']}</span>
                </div>
                <p style='color: #c9d1d9; margin: 8px 0 0 0;'>{row['message']}</p>
            </div>
            """, unsafe_allow_html=True)

            ack_col1, ack_col2 = st.columns([1, 4])
            with ack_col1:
                if st.button(f"Acknowledge #{alert_id}", key=f"ack_btn_{alert_id}", type="secondary"):
                    user = st.session_state.get("username", "operator")
                    repo.acknowledge_alert(alert_id, user=user)
                    st.success(f"Alert #{alert_id} acknowledged by {user}.")
                    st.rerun()

st.markdown("---")

# Full Alert Audit History
st.subheader("📋 Historical Incident Audit Log")
all_alerts = repo.get_alerts(device_id="motor01", only_unacknowledged=False, limit=50)

if not all_alerts.empty:
    display_df = all_alerts[[
        "id", "timestamp", "severity", "title", "acknowledged", "acknowledged_by", "acknowledged_at"
    ]]
    st.dataframe(display_df, use_container_width=True)
else:
    st.info("No recorded alarms in audit history.")

