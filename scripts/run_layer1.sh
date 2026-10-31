#!/usr/bin/env bash
# ==============================================================================
# LAYER 1: Synthetic Telemetry -> MQTT -> CSV Logger -> Streamlit Dashboard
# Verifies basic simulation, publishing, CSV append, and live visualization.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

VENV_PY="$PROJECT_ROOT/.venv/bin/python"
VENV_STREAMLIT="$PROJECT_ROOT/.venv/bin/streamlit"

echo "================================================================================"
echo "⚡ RUNNING LAYER 1: SYNTHETIC DATA -> MQTT -> CSV -> DASHBOARD"
echo "================================================================================"

# Verify simulation scenario generation
echo "Running Layer 1 unit tests..."
"$PROJECT_ROOT/.venv/bin/pytest" tests/test_simulation.py -v

echo -e "\nStarting Layer 1 Ingestion (CSV Logging)..."
PID_SUB=""
PID_PUB=""

cleanup() {
    echo -e "\nStopping Layer 1 test services..."
    [ -n "$PID_PUB" ] && kill -TERM "$PID_PUB" 2>/dev/null || true
    [ -n "$PID_SUB" ] && kill -TERM "$PID_SUB" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Start subscriber writing to CSV
"$VENV_PY" ingestion/mqtt_subscriber.py &
PID_SUB=$!

# Start publisher with mechanical overload scenario
"$VENV_PY" simulation/mqtt_publisher.py --scenario overload --interval 0.5 --count 20 &
PID_PUB=$!

wait "$PID_PUB"
echo "Published 20 sample readings to CSV: data/csv/sensor_telemetry.csv"

# Show CSV contents
head -n 5 data/csv/sensor_telemetry.csv

echo "Launching Streamlit dashboard to inspect CSV telemetry..."
"$VENV_STREAMLIT" run dashboard/app.py --server.port=8501
