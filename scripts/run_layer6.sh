#!/usr/bin/env bash
# ==============================================================================
# LAYER 6: ESP32 Hardware Integration & Sensor Calibration Mode
# Checks USB serial connectivity, verifies pinouts, and switches system to real hardware.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

VENV_PY="$PROJECT_ROOT/.venv/bin/python"

echo "================================================================================"
echo "⚡ RUNNING LAYER 6: ESP32 HARDWARE INTEGRATION & BENCH VALIDATION"
echo "================================================================================"

echo "1. Checking connected USB Serial devices on macOS..."
SERIAL_DEVICES=$(ls /dev/cu.usbserial* /dev/cu.wchusbserial* 2>/dev/null || true)

if [ -z "$SERIAL_DEVICES" ]; then
    echo "⚠️  No physical ESP32 USB serial device detected."
    echo "   Ensure your ESP32 DevKit is plugged in via a data-capable MicroUSB/USB-C cable."
else
    echo "✓ Found ESP32 serial port(s):"
    echo "$SERIAL_DEVICES"
fi

echo -e "\n2. Electrical & Safety Pin Verification Checklist:"
echo "   [ ] MPU6050 SDA connected to GPIO 21, SCL to GPIO 22 (Powered from 3.3V)"
echo "   [ ] DS18B20 DQ connected to GPIO 4 with 4.7kΩ pull-up to 3.3V"
echo "   [ ] ACS712 output connected to GPIO 36 via 10kΩ/20kΩ voltage divider"
echo "   [ ] IR Sensor connected to GPIO 18 (Interrupt pin)"
echo "   [ ] Alert Warning LED on GPIO 2 (with 330Ω resistor to GND)"
echo "   [ ] Alert Piezo Buzzer on GPIO 15 (transistor driven)"
echo "   [ ] 12V DC Motor powered from external 12V 2A supply (COMMON GROUND to ESP32)"

echo -e "\n3. Firmware Compilation & Flashing Instructions:"
echo "   cd firmware/esp32_motor_monitor"
echo "   pio run --target upload"
echo "   pio device monitor -b 115200"

echo -e "\n4. Starting Backend Telemetry Ingestion (Ready for ESP32 MQTT Packets)..."
"$VENV_PY" ingestion/mqtt_subscriber.py
