# Layer 1 — Synthetic Telemetry → MQTT → CSV Logging → Live Dashboard

## 1. Objective
Establish the baseline simulation monitoring pipeline. The system generates realistic, physics-grounded telemetry for a 12V DC motor, transmits readings through a local MQTT broker, logs records into thread-safe CSV files, and provides a live updating Streamlit dashboard without requiring physical hardware or cloud credentials.

---

## 2. Components Implemented

### A. Physics-Grounded Synthetic Generator (`simulation/synthetic_generator.py`)
Generates 7 discrete operational profiles:
1. **Normal Motor Operation**: Nominal armature current ($0.45 - 0.65\,\text{A}$), steady shaft speed ($1950 - 2050\,\text{RPM}$), stable temperature ($35 - 42^\circ\text{C}$), low vibration ($0.05 - 0.12\,g$).
2. **Mechanical Overload**: Elevated current ($1.10 - 1.45\,\text{A}$), reduced shaft speed ($1300 - 1650\,\text{RPM}$), gradual thermal rise.
3. **Excessive Vibration**: High dynamic acceleration ($0.45 - 0.85\,g$) simulating loose mounting or coupling misalignment.
4. **Motor Overheating**: Steep thermal trajectory ($65 - 85^\circ\text{C}$) under continuous elevated load.
5. **Motor Slowdown**: Speed degradation ($800 - 1200\,\text{RPM}$) due to DC bus voltage sag or brush resistance.
6. **Motor Stall (Locked Rotor)**: Massive locked-rotor current surge ($1.80 - 2.20\,\text{A}$), speed collapsing to $0 - 50\,\text{RPM}$.
7. **Sensor Error**: Intermittent acquisition dropouts, out-of-range ADC artifacts, or `sensor_status = "error"`.

### B. MQTT Publisher (`simulation/mqtt_publisher.py`)
- Configurable publication frequency (default 1 Hz).
- CLI scenario selection (`--scenario stall`, `--scenario overload`, etc.).
- Reproducible random seeds for deterministic academic benchmarking.

### C. Thread-Safe CSV Logging (`ingestion/csv_logger.py`)
- Appends telemetry to `data/csv/sensor_telemetry.csv`.
- Automatic CSV header initialization and file rotation safety.

### D. Live Streamlit Visualization (`dashboard/pages/2_Live_Monitoring.py`)
- Polling-based auto-refreshing real-time line charts (Plotly).
- Visual indicators for machine status, active scenario, and connection latency.

---

## 3. Verification & Execution
To run Layer 1 independently:
```bash
./scripts/run_layer1.sh
```
Or execute the automated unit test suite:
```bash
./.venv/bin/pytest tests/test_simulation.py -v
```
