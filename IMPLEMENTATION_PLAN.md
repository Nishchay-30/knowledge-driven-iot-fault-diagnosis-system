# Implementation Plan — Knowledge-Driven IoT-Based Fault Diagnosis System

## Overview
This document specifies the architecture, engineering roadmap, and verification strategy for the end-to-end six-layer industrial IoT fault diagnosis system monitoring a 12V DC motor asset.

---

## 1. Architectural Architecture & Layer Milestones

```mermaid
flowchart TD
    subgraph L1_L2["Layer 1 & 2: Telemetry Ingestion"]
        S1["Synthetic Generator / ESP32 Hardware"] -->|JSON over MQTT| B1["MQTT Broker (Local Mosquitto 1883 / HiveMQ Cloud 8883 TLS)"]
        B1 -->|Telemetry Stream| SUB["Managed Ingestion Subscriber"]
        SUB -->|Raw Log| CSV["CSV Persistence (data/csv/sensor_telemetry.csv)"]
    end

    subgraph L3["Layer 3: Authoritative Database"]
        SUB -->|Deduplicated Insert| SQLITE[("SQLite Database (WAL Mode)")]
        SQLITE --- T1["devices"]
        SQLITE --- T2["sensor_readings"]
        SQLITE --- T3["fault_predictions"]
        SQLITE --- T4["alert_history"]
        SQLITE --- T5["users / system_events"]
    end

    subgraph L4["Layer 4: Industrial Automation"]
        B1 -->|iot/factory/+/sensors| NRED["Node-RED Orchestration Engine"]
        NRED -->|Hysteresis & Cooldown| NRED_ALERT["Alert Dispatch & Recovery"]
        NRED_ALERT -->|iot/factory/+/alerts| B1
    end

    subgraph L5["Layer 5: Knowledge-Driven AI/ML & Dashboard"]
        SUB -->|Windowed Readings| HYBRID["Hybrid Diagnostic Engine"]
        HYBRID -->|Rules Evaluation| RE["Knowledge Rule Engine (YAML Rules)"]
        HYBRID -->|Temporal Features| ML["Scikit-Learn Random Forest"]
        HYBRID -->|Consensus / Conflict Resolution| DIAG_OUT["Prescriptive Diagnosis"]
        DIAG_OUT -->|Store| SQLITE
        DIAG_OUT -->|Publish| B1
        SQLITE --> DASH["Streamlit Industrial Portal (Port 8501)"]
        SQLITE --> FASTAPI["FastAPI REST API (Port 8000)"]
    end

    subgraph L6["Layer 6: Physical ESP32 Hardware"]
        SENSORS["MPU6050 (RMS), DS18B20, ACS712, IR Pulse"] --> ESP32["ESP32 DevKit Microcontroller"]
        ESP32 -->|WiFi + TLS MQTT| B1
        B1 -->|iot/factory/+/alerts (Commands)| ESP32
        ESP32 --> ACT["Status LED / Piezo Buzzer"]
    end
```

---

## 2. Detailed Six-Layer Implementation Breakdown

### Layer 1: Synthetic Telemetry → Local MQTT → CSV Logging → Dashboard
- **Simulation Generator (`simulation/synthetic_generator.py`)**: Reproducible random physics simulation modeling normal motor behavior, mechanical overload, excessive vibration, thermal overheating, slowdown, motor stall, and sensor acquisition anomalies.
- **Publisher (`simulation/mqtt_publisher.py`)**: Paho MQTT publisher with configurable publishing rate, burst intervals, and scenario selection.
- **Ingestion (`ingestion/csv_logger.py`, `ingestion/data_validator.py`)**: Thread-safe CSV append logger with JSON schema validation.
- **Verification**: `tests/test_simulation.py`, `tests/test_mqtt.py`.

### Layer 2: Cloud MQTT Integration (HiveMQ Cloud TLS 8883) with Local Fallback
- **TLS Client (`ingestion/mqtt_client.py`)**: Paho MQTT v2 client with automatic exponential backoff, reconnect handling, TLS v1.2/1.3 wrapper, and fallback to local broker when cloud credentials are unconfigured.
- **Settings (`config/settings.py`)**: Strict environment variable parsing, avoiding hardcoded credentials.
- **Verification**: `tests/test_mqtt.py`.

### Layer 3: Authoritative SQLite Persistence & Analytics
- **Schema (`database/models.py`)**: SQLite in Write-Ahead-Logging (WAL) mode with foreign keys, indexes on `(device_id, timestamp)`, and `UNIQUE(event_id)` deduplication.
- **Repository (`database/repository.py`)**: Centralized repository pattern handling telemetry insertion, historical window queries, alert acknowledgements, and system event logging.
- **Migrations (`database/migrations/`)**: Versioned schema migration script (`001_initial_schema.sql`).
- **Verification**: `tests/test_database.py`.

### Layer 4: Node-RED Automation, Hysteresis & Alert Dispatch
- **Flow Definition (`nodered/flows.json`)**: Importable flow supporting MQTT topic subscription, JSON validation, persistence state tracking, consecutive fault debouncing ($N=3$), cooldown timers (15s), recovery events, and alert publishing.
- **Docker Integration (`docker-compose.yml`)**: Multi-container compose configuration running Mosquitto, Node-RED, FastAPI, and Streamlit.
- **Verification**: `tests/test_alerts.py`.

### Layer 5: Knowledge-Driven AI/ML Expert System & Multi-Page Dashboard
- **Declarative Knowledge Base (`config/knowledge_base.yaml`, `diagnosis/rule_engine.py`)**: Priority-ranked physics equations evaluating load, thermal stress, locked rotor, dynamic unbalance, and transducer fault hypotheses.
- **Machine Learning Pipeline (`ml/features.py`, `ml/train.py`, `ml/predict.py`, `ml/evaluate.py`)**: Rolling feature extractor (temperature drift, vibration RMS trends, speed drops, current variance), baseline vs Random Forest training, group holdout testing, and model persistence.
- **Hybrid Consensus Reconciler (`diagnosis/hybrid_engine.py`)**: Combines rule engine determinism with ML probabilistic scores, highlighting diagnostic conflicts and uncertainties.
- **Security & RBAC (`backend/auth/security.py`)**: PBKDF2-HMAC-SHA256 password hashing with salt, rate-limiting, and token authentication.
- **Streamlit Industrial SaaS Dashboard (`dashboard/`)**: Dark theme (GitHub/Grafana palette), live polling, real-time charts, diagnosis breakdowns, historical analytics, alert acknowledgement, system settings, and model metrics.
- **Verification**: `tests/test_rules.py`, `tests/test_ml.py`, `tests/test_api.py`.

### Layer 6: ESP32 Hardware Integration & Physical Alerts
- **Firmware (`firmware/esp32_motor_monitor/`)**: PlatformIO C++ firmware with non-blocking WiFi/MQTT reconnection, I2C MPU6050 vibration RMS calculation (sampling window 100 samples), OneWire DS18B20 temperature, ACS712 zero-offset calibrated current, and interrupt-driven optical RPM measurement.
- **Physical Indication**: Listens to `iot/factory/motor01/alerts`, toggling warning LEDs and buzzer alert tones on CRITICAL diagnostic flags.
- **Documentation (`docs/HARDWARE_WIRING.md`)**: Comprehensive pinouts, 3.3V/5V logic conversion, optoisolator protection, separate 12V motor power rail, and safety checklists.

---

## 3. Execution & Verification Roadmap

1. **Verify Existing Tests**: Confirm baseline 22 unit tests pass across all functional modules.
2. **Add Missing Modules**:
   - `ml/evaluate.py`: Standalone evaluation script with CLI output.
   - `diagnosis/recommendations.py`: Prescriptive maintenance engine.
   - `diagnosis/knowledge_base.py`: Knowledge base inspector and query interface.
   - `database/migrations/001_initial_schema.sql` & `migrate.py`.
3. **Build ESP32 Firmware & Hardware Files**:
   - `firmware/esp32_motor_monitor/platformio.ini`
   - `firmware/esp32_motor_monitor/include/config.h`
   - `firmware/esp32_motor_monitor/src/main.cpp`
   - `firmware/esp32_motor_monitor/README.md`
4. **Create Shell Launch Scripts (`scripts/`)**:
   - `scripts/setup.sh`
   - `scripts/run_demo.sh`
   - `scripts/run_layer1.sh` through `scripts/run_layer6.sh`
5. **Produce Engineering Documentation (`docs/` & `README.md`)**:
   - `README.md`
   - `docs/ARCHITECTURE.md`
   - `docs/LAYER_1.md` through `docs/LAYER_6.md`
   - `docs/HARDWARE_WIRING.md`
   - `docs/API.md`
   - `docs/TESTING.md`
   - `docs/TROUBLESHOOTING.md`
   - `docs/PROJECT_REPORT.md`
6. **Execute Full Test & Verification Suite**:
   - Run pytest and record detailed terminal logs in `PROJECT_STATUS.md`.
