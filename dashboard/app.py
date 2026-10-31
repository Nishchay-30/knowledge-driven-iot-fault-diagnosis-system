"""
Streamlit Multi-Page Main Application.
Handles user session authentication, dark industrial CSS injection, and sidebar navigation.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from config.settings import settings
from backend.auth.security import auth_manager

st.set_page_config(
    page_title="IoT Fault Diagnosis System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS
css_path = Path(__file__).parent / "styles" / "theme.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Session state initialization
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None


def render_login_form():
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>⚡ Industrial Motor Diagnostic Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8b949e;'>Knowledge-Driven IoT Fault Diagnosis System — 12V DC Motor Asset</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.subheader("Secure Operator Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Sign In", type="primary", use_container_width=True):
            if username and password:
                session = auth_manager.authenticate_user(username, password)
                if session and "error" not in session:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = session["username"]
                    st.session_state["role"] = session["role"]
                    st.session_state["token"] = session["token"]
                    st.success(f"Welcome, {session['username']} ({session['role']})!")
                    st.rerun()
                elif session and "error" in session:
                    st.error(session["error"])
                else:
                    st.error("Invalid username or password.")
            else:
                st.warning("Please enter both username and password.")
        
        st.markdown("---")
        st.caption("Default local credentials:")
        st.caption("• **Admin**: `admin` / `Admin@2026`")
        st.caption("• **Operator**: `operator` / `Operator@2026`")
        st.markdown("</div>", unsafe_allow_html=True)


def main():
    if not st.session_state["authenticated"]:
        render_login_form()
        return

    # Sidebar Header
    st.sidebar.markdown(f"### ⚡ Motor Condition Monitor")
    st.sidebar.markdown(f"**Operator:** `{st.session_state['username']}` ({st.session_state['role']})")
    
    # Connection badge
    mqtt_cfg = settings.get_effective_mqtt_config()
    broker_label = "HiveMQ Cloud (TLS)" if mqtt_cfg["broker_type"] == "hivemq_cloud" else "Local Mosquitto (1883)"
    st.sidebar.caption(f"Broker: **{broker_label}**")
    st.sidebar.caption(f"Mode: **{settings.OPERATION_MODE.upper()}**")

    if st.sidebar.button("Sign Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["role"] = None
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Navigation")
    st.sidebar.info("Select a view from the sidebar pages above to inspect live telemetry, rule explanations, or machine learning diagnostics.")

    # Redirect to Overview by default
    st.title("⚡ Knowledge-Driven Industrial Fault Diagnosis System")
    st.markdown("""
    Welcome to the condition-monitoring and diagnostic platform for industrial 12V DC motor assets.
    Use the navigation menu in the left sidebar to explore:
    - **1 Overview**: Real-time asset health KPIs, operating states, and active hypotheses.
    - **2 Live Monitoring**: High-frequency multi-sensor trend charts and scenario controls.
    - **3 Fault Diagnosis**: Hybrid knowledge-driven rule reasoning and Random Forest predictions.
    - **4 Historical Analytics**: Query persistent SQLite records, multi-sensor overlays, and CSV export.
    - **5 Alerts**: Active alarm queue with operator acknowledgement workflows.
    - **6 Settings**: MQTT broker configuration, thresholds editor, and hardware/simulation toggle.
    - **7 Model Performance**: Confusion matrix, classification metrics, and synthetic limitations.
    """)


if __name__ == "__main__":
    main()

