#!/usr/bin/env bash
# ==============================================================================
# LAYER 5: Knowledge-Driven AI/ML Expert Rules, Login & Multi-Page Dashboard
# Runs rule evaluation, ML inference metrics, and launches backend API + Dashboard.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

VENV_PY="$PROJECT_ROOT/.venv/bin/python"
VENV_STREAMLIT="$PROJECT_ROOT/.venv/bin/streamlit"

echo "================================================================================"
echo "⚡ RUNNING LAYER 5: KNOWLEDGE-DRIVEN AI/ML, AUTHENTICATION & DASHBOARD"
echo "================================================================================"

# Run test suites for rules, ML, and API
echo "Running Layer 5 comprehensive test suites..."
"$PROJECT_ROOT/.venv/bin/pytest" tests/test_rules.py tests/test_ml.py tests/test_api.py -v

# Run Model Evaluation
echo -e "\nEvaluating Machine Learning Model:"
"$VENV_PY" ml/evaluate.py

echo -e "\nStarting FastAPI Backend Service (Port 8000)..."
PID_API=""
PID_DASH=""

cleanup() {
    echo -e "\nStopping Layer 5 services..."
    [ -n "$PID_API" ] && kill -TERM "$PID_API" 2>/dev/null || true
    [ -n "$PID_DASH" ] && kill -TERM "$PID_DASH" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

"$VENV_PY" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level warning &
PID_API=$!

sleep 2

echo "Launching Streamlit Industrial Diagnostic Dashboard (Port 8501)..."
"$VENV_STREAMLIT" run dashboard/app.py --server.port=8501
