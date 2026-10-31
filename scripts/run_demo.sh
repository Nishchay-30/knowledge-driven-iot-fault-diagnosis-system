#!/usr/bin/env bash
# ==============================================================================
# One-Command Local Demo Launcher
# Knowledge-Driven IoT Fault Diagnosis System
# Launches:
#   1. Ingestion Service (Telemetry validator, SQLite/CSV writer, Hybrid AI Engine)
#   2. Synthetic Publisher (Simulating dynamic motor operating scenarios)
#   3. Streamlit Industrial Dashboard (Port 8501)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

VENV_PY="$PROJECT_ROOT/.venv/bin/python"
VENV_STREAMLIT="$PROJECT_ROOT/.venv/bin/streamlit"

if [ ! -f "$VENV_PY" ]; then
    echo "Virtual environment not found. Running setup.sh first..."
    bash "$SCRIPT_DIR/setup.sh"
fi

echo "================================================================================"
echo "⚡ Starting Knowledge-Driven IoT Fault Diagnosis System (Local Demo Mode)"
echo "Mode: Local Simulation & Diagnostics"
echo "================================================================================"

PID_SUB=""
PID_PUB=""
PID_DASH=""

cleanup() {
    echo -e "\n\nShutting down all demonstration processes gracefully..."
    [ -n "$PID_PUB" ] && kill -TERM "$PID_PUB" 2>/dev/null || true
    [ -n "$PID_SUB" ] && kill -TERM "$PID_SUB" 2>/dev/null || true
    [ -n "$PID_DASH" ] && kill -TERM "$PID_DASH" 2>/dev/null || true
    wait 2>/dev/null || true
    echo "All processes cleanly stopped. Goodbye."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 1. Start Telemetry Ingestion Service in background
echo "Starting Telemetry Ingestion & Diagnostic Consumer..."
"$VENV_PY" ingestion/mqtt_subscriber.py > /dev/null 2>&1 &
PID_SUB=$!
echo "✓ Ingestion Service started (PID: $PID_SUB)"

# 2. Start Synthetic Data Publisher in background (cycles scenarios)
echo "Starting Synthetic Telemetry Publisher (motor01)..."
"$VENV_PY" simulation/mqtt_publisher.py --scenario normal --interval 1.0 > /dev/null 2>&1 &
PID_PUB=$!
echo "✓ Synthetic Generator started (PID: $PID_PUB)"

# Wait 2 seconds for services to establish loopback
sleep 2

# 3. Launch Streamlit Industrial Monitoring Portal
echo "Launching Streamlit Monitoring Dashboard at http://localhost:8501..."
echo "Sign in using: admin / Admin@2026 or operator / Operator@2026"
echo "Press Ctrl+C to stop all services."
echo "================================================================================"

"$VENV_STREAMLIT" run dashboard/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --browser.gatherUsageStats=false
