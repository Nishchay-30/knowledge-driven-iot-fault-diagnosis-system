# Troubleshooting Guide — Knowledge-Driven IoT Fault Diagnosis System

This document outlines common operational issues, diagnostics procedures, and recovery steps across all six layers.

---

## 1. MQTT Connectivity & Broker Issues

### Issue A: "Connection refused (1883)"
- **Cause**: Local Mosquitto broker is not running.
- **Resolution**:
  - If using Docker: run `docker compose up mosquitto -d`.
  - Alternatively, in unit tests and simulation mode, the Python `ManagedMQTTClient` logs a connection warning and continues gracefully.
  - To test connection manually: `nc -zv 127.0.0.1 1883`.

### Issue B: HiveMQ Cloud TLS Handshake Failure (8883)
- **Cause**: Incorrect cluster host, expired credentials, or missing TLS port.
- **Resolution**:
  - Inspect `.env` file. Confirm `HIVEMQ_HOST` does not include `mqtt://` or `ssl://` prefix.
  - Verify port is set to `8883`.
  - If credentials are unknown, set `USE_LOCAL_BROKER=true` in `.env` to operate in local fallback mode.

---

## 2. Database & Storage Issues

### Issue A: "database is locked" (SQLite)
- **Cause**: Long-running read transaction blocking writes when WAL mode is inactive.
- **Resolution**:
  - The repository automatically executes `PRAGMA journal_mode = WAL`.
  - Ensure all database access uses the context manager in `database/connection.py` (`with db_manager.session() as conn:`), which guarantees automatic transaction commits and connection closing.

### Issue B: "Duplicate event_id skipped"
- **Cause**: This is **normal expected behavior** enforcing telemetry deduplication. If both Node-RED and Python subscriber listen to the same topic, only the first arrival is inserted; duplicates are silently suppressed.

---

## 3. Machine Learning & Diagnostic Engine Issues

### Issue A: "ML model unavailable. Operating in deterministic rules-only mode."
- **Cause**: The model artifact `ml/models/random_forest_model.joblib` has not been generated.
- **Resolution**:
  - Run the training pipeline:
    ```bash
    ./.venv/bin/python ml/train.py
    ```
  - The hybrid engine automatically handles missing models by falling back cleanly to deterministic engineering rules.

### Issue B: "Conflict detected between Rule Engine and ML Classifier"
- **Cause**: Non-linear sensor noise or edge operating values triggered differing classifications.
- **Resolution**:
  - This is an **intentional design feature**. Check `dashboard/pages/3_Fault_Diagnosis.py` to see the conflict explanation and supporting measurements. The engine automatically adopts the higher-severity classification for safety.

---

## 4. Hardware & ESP32 Issues

### Issue A: "MPU6050 Accelerometer connection failed"
- **Cause**: Loose I2C DuPont wires, incorrect pin mapping, or unpowered sensor.
- **Resolution**:
  - Check wiring: SDA $\to$ GPIO 21, SCL $\to$ GPIO 22.
  - Verify MPU6050 VCC is connected to **3.3V** (or 5V if module contains an onboard 3.3V LDO).
  - Check that MPU6050 AD0 pin is tied to GND (sets I2C address to `0x68`).

### Issue B: "No temperature sensor found (DS18B20)"
- **Cause**: Missing 4.7kΩ pull-up resistor between data (DQ) and 3.3V.
- **Resolution**:
  - 1-Wire buses require an external pull-up resistor (4.7kΩ nominal, 2.2kΩ–10kΩ acceptable) between GPIO 4 and 3.3V.

### Issue C: Erratic or Constant 0 RPM
- **Cause**: Misaligned optical slot sensor or beam obstructed.
- **Resolution**:
  - Confirm the slotted disc rotates cleanly between the optical transmitter and phototransistor.
  - Verify optical sensor output pin is connected to GPIO 18 and pulls LOW when a disc blade interrupts the beam.

### Issue D: ESP32 ADC Reading 4095 on ACS712
- **Cause**: 5V output applied directly to ESP32 ADC pin without voltage divider.
- **Resolution**:
  - **Immediately disconnect!** Insert a 10kΩ / 20kΩ voltage divider between ACS712 OUT and GPIO 36.
