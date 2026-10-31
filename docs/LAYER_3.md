# Layer 3 — SQLite Historical Database & Analytics Repository

## 1. Objective
Establish an ACID-compliant, persistent relational database using SQLite in Write-Ahead Logging (WAL) mode. The database serves as the single source of truth for telemetry streams, hybrid diagnostic predictions, active and historical alerts, operator acknowledgements, user access control, and audit logs.

---

## 2. Relational Schema Architecture

```mermaid
erDiagram
    DEVICES ||--o{ SENSOR_READINGS : emits
    DEVICES ||--o{ FAULT_PREDICTIONS : evaluates
    DEVICES ||--o{ FAULT_EVENTS : logs
    DEVICES ||--o{ ALERT_HISTORY : triggers

    DEVICES {
        text device_id PK
        text name
        text type
        text driver
        real rated_voltage_v
        real rated_current_a
        real rated_rpm
        text location
        text created_at
    }

    SENSOR_READINGS {
        integer id PK
        text event_id UK
        text device_id FK
        text timestamp
        text source
        real temperature_c
        real vibration_rms_g
        real current_a
        real rpm
        text sensor_status
        text created_at
    }

    FAULT_PREDICTIONS {
        integer id PK
        text event_id
        text device_id FK
        text timestamp
        text rule_fault
        text rule_severity
        text ml_fault
        real ml_confidence
        text hybrid_fault
        text hybrid_severity
        text explanation
        text recommended_action
        integer conflict_detected
        text created_at
    }

    ALERT_HISTORY {
        integer id PK
        text device_id
        text timestamp
        text severity
        text title
        text message
        integer acknowledged
        text acknowledged_by
        text acknowledged_at
        text created_at
    }

    USERS {
        integer id PK
        text username UK
        text password_hash
        text salt
        text role
        integer is_active
        text created_at
        text last_login
    }

    SYSTEM_EVENTS {
        integer id PK
        text timestamp
        text event_type
        text component
        text message
        text details
        text created_at
    }
```

---

## 3. Key Design Decisions

1. **Write-Ahead Logging (WAL)**: `PRAGMA journal_mode = WAL` enables concurrent readers while a single writer operates without blocking the UI.
2. **Event Deduplication**: The `event_id UNIQUE` constraint drops duplicate telemetry packets originating from network retransmissions.
3. **Historical Time-Range Queries**: The composite index `(device_id, timestamp DESC)` ensures efficient historical analytics and slicing across arbitrary date-time windows.
4. **Data Migrations**: Versioned SQL migrations (`database/migrations/001_initial_schema.sql`) are applied deterministically via `database/migrations/migrate.py`.

---

## 4. Verification & Execution
To run database migrations and execute the verification test suite:
```bash
./scripts/run_layer3.sh
```
Or run the dedicated pytest suite:
```bash
./.venv/bin/pytest tests/test_database.py -v
```
