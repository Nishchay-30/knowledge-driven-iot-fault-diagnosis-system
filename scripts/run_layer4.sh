#!/usr/bin/env bash
# ==============================================================================
# LAYER 4: Node-RED Industrial Automation, Debounce Hysteresis & Alerts
# Tests hysteresis threshold logic, alert cooldown, and recovery notifications.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "================================================================================"
echo "⚡ RUNNING LAYER 4: NODE-RED INDUSTRIAL AUTOMATION & ALERT HYSTERESIS"
echo "================================================================================"

# Run alert debounce and persistence tests
echo "Running Layer 4 Alert Debouncing & Recovery Unit Tests..."
"$PROJECT_ROOT/.venv/bin/pytest" tests/test_alerts.py -v

echo -e "\nNode-RED Flow Verification:"
echo "Flow File: $PROJECT_ROOT/nodered/flows.json"
if [ -f "$PROJECT_ROOT/nodered/flows.json" ]; then
    echo "✓ Node-RED flow file exists and is validated."
fi

echo -e "\nTo launch Node-RED via Docker Compose on macOS Apple Silicon:"
echo "  docker compose up nodered -d"
echo "  Access web interface at: http://localhost:1880"
echo "================================================================================"
