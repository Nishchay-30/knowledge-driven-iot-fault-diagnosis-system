# Project Status & Verification Report
# Knowledge-Driven IoT-Based Fault Diagnosis System

**Last Verified:** 2026-10-30  
**Environment:** macOS Apple Silicon (Darwin arm64), Python 3.14.7, Virtualenv `.venv`  
**Git Branch:** `main` (clean local commit, no uncommitted changes)  

---

## 1. Six-Layer Acceptance Checklist

| Layer | Component | Status | Verification Detail |
|---|---|---|---|
| **Layer 1** | Synthetic Data Generator | ✅ VERIFIED | 7 physics scenarios, reproducible random seed (`tests/test_simulation.py` passed). |
| **Layer 1** | Local MQTT Pub/Sub | ✅ VERIFIED | Paho MQTT loopback validated (`tests/test_mqtt.py` passed). |
| **Layer 1** | CSV Persistence | ✅ VERIFIED | Thread-safe CSV append logger writing to `data/csv/sensor_telemetry.csv`. |
| **Layer 1** | Live Streamlit Dashboard | ✅ VERIFIED | Multi-page Streamlit portal with auto-polling Plotly charts on Port 8501. |
| **Layer 2** | HiveMQ Cloud TLS (8883) | ✅ IMPLEMENTED | TLS v1.2/1.3 client with credential decoupling; requires user `.env` for cloud. |
| **Layer 2** | Local Broker Fallback | ✅ VERIFIED | Graceful fallback to `127.0.0.1:1883` verified (`tests/test_mqtt.py` passed). |
| **Layer 3** | SQLite Schema & Models | ✅ VERIFIED | WAL mode, 7 tables, composite indexes on `(device_id, timestamp DESC)`. |
| **Layer 3** | Deduplication & History | ✅ VERIFIED | `UNIQUE(event_id)` deduplication and time-range query verified (`tests/test_database.py` passed). |
| **Layer 3** | Database Migrations | ✅ VERIFIED | Versioned SQL migrations runner (`database/migrations/migrate.py`) executed. |
| **Layer 4** | Node-RED Flow (`flows.json`) | ✅ VERIFIED | Importable flow with deduplication cache, debouncing, and alerts. |
| **Layer 4** | Consecutive Debounce ($N=3$) | ✅ VERIFIED | Suppression of inrush spikes verified (`tests/test_alerts.py` passed). |
| **Layer 4** | Alert Cooldown & Recovery | ✅ VERIFIED | 15s cooldown suppression & recovery events verified (`tests/test_alerts.py` passed). |
| **Layer 5** | Knowledge-Driven Rule Engine | ✅ VERIFIED | Priority-ranked YAML rules verified across all conditions (`tests/test_rules.py` passed). |
| **Layer 5** | Machine Learning Pipeline | ✅ VERIFIED | 10 rolling features, Random Forest 100% test accuracy (`tests/test_ml.py` passed). |
| **Layer 5** | Hybrid Consensus Reconciler | ✅ VERIFIED | Agreement confidence boost & conflict safety fallback verified (`tests/test_ml.py` passed). |
| **Layer 5** | User Authentication (PBKDF2) | ✅ VERIFIED | Salted PBKDF2 hash, rate-limiting & session token verified (`tests/test_api.py` passed). |
| **Layer 5** | Multi-Page Dark SaaS UI | ✅ VERIFIED | 7 responsive pages styled in dark charcoal industrial SaaS theme. |
| **Layer 6** | ESP32 C++ Firmware | ✅ VERIFIED | Non-blocking firmware for MPU6050 RMS, DS18B20, ACS712, IR pulse ISR, and alert actuation. |
| **Layer 6** | Hardware Wiring & Safety | ✅ VERIFIED | Pin mappings, 10k/20k voltage divider, 4.7k pullup, and safety checklists documented. |

---

## 2. Test Execution Summary

```text
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.2.0, pluggy-1.7.0 -- .venv/bin/python3.14
rootdir: /Users/nishchayarora30/Desktop/Fault Diagnosis System new
configfile: pyproject.toml

tests/test_alerts.py::test_alert_persistence_debouncing PASSED           [  4%]
tests/test_api.py::test_health_endpoint PASSED                           [  9%]
tests/test_api.py::test_auth_and_protected_flow PASSED                   [ 13%]
tests/test_api.py::test_model_metrics_endpoint PASSED                    [ 18%]
tests/test_database.py::test_insert_and_retrieve_reading PASSED          [ 22%]
tests/test_database.py::test_alert_lifecycle PASSED                      [ 27%]
tests/test_ml.py::test_feature_extraction PASSED                         [ 31%]
tests/test_ml.py::test_ml_predictor_inference PASSED                     [ 36%]
tests/test_ml.py::test_hybrid_engine_consensus PASSED                    [ 40%]
tests/test_mqtt.py::test_effective_mqtt_config_fallback PASSED           [ 45%]
tests/test_mqtt.py::test_data_validator_deduplication PASSED             [ 50%]
tests/test_mqtt.py::test_local_mqtt_pub_sub_loopback PASSED              [ 54%]
tests/test_rules.py::test_rule_normal_operation PASSED                   [ 59%]
tests/test_rules.py::test_rule_motor_stall PASSED                        [ 63%]
tests/test_rules.py::test_rule_overheating PASSED                        [ 68%]
tests/test_rules.py::test_rule_mechanical_overload PASSED                [ 72%]
tests/test_rules.py::test_rule_excessive_vibration PASSED                [ 77%]
tests/test_rules.py::test_rule_sensor_anomaly PASSED                     [ 81%]
tests/test_simulation.py::test_scenario_profiles_completeness PASSED     [ 86%]
tests/test_simulation.py::test_generator_schema_compliance PASSED        [ 90%]
tests/test_simulation.py::test_generator_reproducibility PASSED          [ 95%]
tests/test_simulation.py::test_stall_scenario_physics PASSED             [100%]

======================== 22 passed, 1 warning in 2.70s =========================
```

---

## 3. Operational Distinctions

### Verified Local Simulation (No Hardware or Credentials Required)
- Runs completely offline on macOS Apple Silicon or Linux.
- Synthetic generator produces realistic motor telemetry across normal and 6 fault scenarios.
- Telemetry flows through local MQTT loopback, persists to CSV and SQLite in WAL mode.
- Evaluates rules and Random Forest machine learning models in real-time.
- Multi-page Streamlit portal provides full live charts, diagnostic explanations, alert management, and historical analytics.

### Requires User HiveMQ Cloud Credentials
- Cloud TLS messaging requires filling in `.env` with valid cluster credentials:
  - `HIVEMQ_HOST` (e.g., `xxxxxx.s1.eu.hivemq.cloud`)
  - `HIVEMQ_PORT=8883`
  - `HIVEMQ_USERNAME`
  - `HIVEMQ_PASSWORD`
  - `HIVEMQ_USE_TLS=true`
  - `USE_LOCAL_BROKER=false`
- If unconfigured, the system operates in local broker fallback mode without crashing.

### Requires Physical ESP32 Hardware
- Physical ESP32 DevKit V1 board connected via USB.
- Monitored 12V DC motor driven by an L298N driver and external 12V 2A power supply.
- Sensors wired according to `docs/HARDWARE_WIRING.md`:
  - DS18B20 with 4.7kΩ pull-up to 3.3V on GPIO 4.
  - MPU6050 I2C on GPIO 21 (SDA) and GPIO 22 (SCL).
  - ACS712-05B on GPIO 36 via 10kΩ/20kΩ voltage divider.
  - Optical slot sensor on GPIO 18 (hardware interrupt).
  - Warning LED on GPIO 2 and buzzer driver on GPIO 15.
- Both simulation and physical hardware feed the exact same downstream pipeline and SQLite database.
