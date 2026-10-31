#!/usr/bin/env bash
# ==============================================================================
# LAYER 3: SQLite Persistent Historical Database & Queries
# Verifies migrations, deduplication, historical time-range queries, and WAL mode.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

VENV_PY="$PROJECT_ROOT/.venv/bin/python"

echo "================================================================================"
echo "⚡ RUNNING LAYER 3: SQLITE PERSISTENT DATABASE & HISTORICAL ANALYTICS"
echo "================================================================================"

# Apply migrations
echo "Executing database migrations..."
"$VENV_PY" database/migrations/migrate.py

# Run Database test suite
echo -e "\nRunning Layer 3 Database tests..."
"$PROJECT_ROOT/.venv/bin/pytest" tests/test_database.py -v

# Inspect Database state
echo -e "\nDatabase Statistics Summary:"
"$VENV_PY" -c "
from database.repository import repo
readings = repo.get_recent_readings('motor01', limit=10)
alerts = repo.get_alerts('motor01', limit=5)
preds = repo.get_recent_predictions('motor01', limit=5)
print(f'Total Sensor Readings in DB:    {len(readings)}')
print(f'Total Active/Logged Alerts:    {len(alerts)}')
print(f'Total Hybrid Predictions in DB: {len(preds)}')
"
echo "================================================================================"
