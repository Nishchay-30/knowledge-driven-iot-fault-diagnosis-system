# Testing Methodology & Acceptance Test Guide

## 1. Testing Framework Overview
The system utilizes `pytest` along with `unittest.mock` for comprehensive automated verification. All tests run in isolated environments without modifying persistent database production data or requiring live cloud / hardware connections.

---

## 2. Test Suites Summary

| Test Module | Coverage Scope | Verified Invariants |
|---|---|---|
| `tests/test_simulation.py` | Synthetic Data Generation | Schema adherence, reproducibility with fixed seeds, 7 fault scenario profiles, stall physics. |
| `tests/test_mqtt.py` | MQTT Client & Ingestion | Graceful local fallback when cloud credentials are empty, payload deduplication, loopback publishing. |
| `tests/test_database.py` | SQLite Persistence | Table initialization, WAL mode, deduplication on `event_id`, time-range queries, alert lifecycle. |
| `tests/test_rules.py` | Knowledge Rule Engine | Declarative rule triggering, priority ordering, normal/overload/vibration/overheating/stall conditions. |
| `tests/test_ml.py` | Machine Learning & Features | Rolling feature extraction, Random Forest inference, consensus agreement, conflict reconciliation. |
| `tests/test_alerts.py` | Alert Orchestration | Consecutive reading debouncing ($N=3$), 15-second cooldown suppression, critical bypass, recovery logic. |
| `tests/test_api.py` | REST API Endpoints | Health check, login authentication, invalid token rejection, protected routes, model metrics endpoint. |

---

## 3. How to Run the Automated Tests

### Run All Tests
```bash
./.venv/bin/pytest tests/ -v
```

### Run Layer-Specific Test Suites
```bash
# Layer 1: Simulation
./.venv/bin/pytest tests/test_simulation.py -v

# Layer 2: MQTT & Fallback
./.venv/bin/pytest tests/test_mqtt.py -v

# Layer 3: Database & Deduplication
./.venv/bin/pytest tests/test_database.py -v

# Layer 4: Alerts & Hysteresis
./.venv/bin/pytest tests/test_alerts.py -v

# Layer 5: Rules, ML & API
./.venv/bin/pytest tests/test_rules.py tests/test_ml.py tests/test_api.py -v
```

---

## 4. End-to-End Integration Verification Workflow

### Step 1: Initialize Database & Default Admin
```bash
./.venv/bin/python database/migrations/migrate.py
./.venv/bin/python scripts/init_admin.py
```

### Step 2: Evaluate Machine Learning Model
```bash
./.venv/bin/python ml/evaluate.py
```

### Step 3: Launch Local Ingestion Pipeline & Simulation
```bash
./scripts/run_demo.sh
```
1. Open `http://localhost:8501` in your browser.
2. Sign in with username `admin` and password `Admin@2026`.
3. Select **Live Monitoring** $\to$ observe real-time updating charts.
4. Select **Fault Diagnosis** $\to$ observe Rule + ML consensus and supporting measurements.
5. Select **Alerts** $\to$ click **Acknowledge** on any raised alert.
