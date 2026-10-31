"""
Settings & Administration Page.
Allows reviewing MQTT broker status, physical motor ratings, thresholds, and operational mode.
"""

import sys
import yaml
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from config.settings import settings
from database.connection import db_manager

st.set_page_config(page_title="Settings | Administration", page_icon="⚡", layout="wide")

if not st.session_state.get("authenticated", False):
    st.warning("Please sign in from the main portal.")
    st.stop()

st.title("⚙️ System Settings & Asset Configuration")

# Operational Mode
st.subheader("1. Operational Mode")
mode_col1, mode_col2 = st.columns(2)
with mode_col1:
    st.markdown(f"**Current Mode:** `{settings.OPERATION_MODE.upper()}`")
    st.caption("• **Simulation Mode**: Generates synthetic motor data with continuous physics.")
    st.caption("• **Real Hardware Mode**: Reads live physical telemetry from ESP32 DevKit.")

with mode_col2:
    st.info("Mode toggle is controlled via `.env` (`OPERATION_MODE=simulation` or `OPERATION_MODE=hardware`). Both modes feed the exact same downstream pipeline.")

st.markdown("---")

# MQTT Broker Configuration
st.subheader("2. MQTT Broker & Connectivity")
mqtt_cfg = settings.get_effective_mqtt_config()

b_col1, b_col2, b_col3 = st.columns(3)
with b_col1:
    st.metric("Broker Type", mqtt_cfg["broker_type"].replace("_", " ").title())
with b_col2:
    st.metric("Host", mqtt_cfg["host"])
with b_col3:
    st.metric("Port", f"{mqtt_cfg['port']} (TLS: {mqtt_cfg['use_tls']})")

if mqtt_cfg["broker_type"] == "hivemq_cloud":
    st.success("Connected to HiveMQ Cloud with TLS 1.2/1.3.")
else:
    st.warning("Using Local Mosquitto Broker fallback (zero cloud credential dependency).")

st.markdown("---")

# Device Specifications
st.subheader("3. Registered Device Specifications (Motor 01)")
if settings.DEVICES_FILE.exists():
    with open(settings.DEVICES_FILE, "r") as f:
        dev_data = yaml.safe_load(f) or {}
    st.json(dev_data)

st.markdown("---")

# Thresholds Configuration
st.subheader("4. Operational Thresholds Configuration")
if settings.THRESHOLDS_FILE.exists():
    with open(settings.THRESHOLDS_FILE, "r") as f:
        thresh_data = yaml.safe_load(f) or {}
    st.json(thresh_data)

