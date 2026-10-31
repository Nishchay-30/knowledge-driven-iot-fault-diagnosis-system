#!/usr/bin/env bash
# ==============================================================================
# LAYER 2: Cloud MQTT Integration (HiveMQ Cloud TLS 8883) with Local Fallback
# Tests TLS connection, credentials, and message routing.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

VENV_PY="$PROJECT_ROOT/.venv/bin/python"

echo "================================================================================"
echo "⚡ RUNNING LAYER 2: HIVEMQ CLOUD TLS (8883) & FALLBACK BROKER"
echo "================================================================================"

# Execute MQTT test suite
echo "Running Layer 2 MQTT & fallback tests..."
"$PROJECT_ROOT/.venv/bin/pytest" tests/test_mqtt.py -v

# Inspect configured MQTT credentials
echo -e "\nChecking Broker Configuration:"
"$VENV_PY" -c "
from config.settings import settings
cfg = settings.get_effective_mqtt_config()
print('Broker Type:', cfg['broker_type'])
print('Host:       ', cfg['host'])
print('Port:       ', cfg['port'])
print('TLS Enabled:', cfg.get('use_tls', False))
print('HiveMQ Cloud Configured:', settings.is_hivemq_configured)
if not settings.is_hivemq_configured:
    print('Notice: Operating in Local Broker Fallback mode. To connect to HiveMQ Cloud, update .env.')
"
echo "================================================================================"
