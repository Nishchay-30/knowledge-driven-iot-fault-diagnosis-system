#!/usr/bin/env bash
# ==============================================================================
# Setup Script for Knowledge-Driven IoT Fault Diagnosis System
# Compatible with macOS Apple Silicon (arm64) and Linux
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "================================================================================"
echo "⚡ Setting up Knowledge-Driven IoT Fault Diagnosis System"
echo "Project Root: $PROJECT_ROOT"
echo "================================================================================"

# 1. Verify Python Version
PYTHON_BIN="python3"
if ! command -v "$PYTHON_BIN" &>/dev/null; then
    echo "❌ Error: python3 not found in PATH."
    exit 1
fi

PY_VER=$($PYTHON_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✓ Detected Python version: $PY_VER"

# 2. Virtual Environment Setup
VENV_DIR="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    $PYTHON_BIN -m venv "$VENV_DIR"
fi

VENV_PY="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# 3. Upgrade pip and install dependencies
echo "Installing project requirements..."
"$VENV_PIP" install --quiet --upgrade pip setuptools wheel
"$VENV_PIP" install --quiet -r requirements.txt

# 4. Create necessary storage folders
echo "Creating required directory structure..."
mkdir -p data/csv data/sqlite data/synthetic ml/models docs/assets

# 5. Initialize .env if missing
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# 6. Database Migrations & Initial Setup
echo "Applying database schema and migrations..."
"$VENV_PY" database/migrations/migrate.py

# 7. Seed Default Admin & Operator Accounts
echo "Seeding default security credentials..."
"$VENV_PY" scripts/init_admin.py

# 8. Train Machine Learning Model if Missing
if [ ! -f "ml/models/random_forest_model.joblib" ]; then
    echo "Training initial Random Forest fault diagnosis model..."
    "$VENV_PY" ml/train.py
else
    echo "✓ Trained machine learning model bundle already present."
fi

# 9. Verify Installation with Test Suite
echo "Running validation unit tests..."
"$VENV_DIR/bin/pytest" tests -q

echo "================================================================================"
echo "✅ Setup successfully completed!"
echo "Run './scripts/run_demo.sh' to launch the one-command local demonstration."
echo "================================================================================"
