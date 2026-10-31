# REST API Documentation — Knowledge-Driven IoT Fault Diagnosis System

The backend provides a FastAPI-powered REST API (Port 8000) for telemetry queries, hybrid diagnoses, alert lifecycle management, and system health status.

---

## 1. Authentication Endpoints

### `POST /api/auth/login`
Authenticates an operator or administrator using salted PBKDF2 hashing.

- **Request Body:**
  ```json
  {
    "username": "admin",
    "password": "Admin@2026"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "token": "64_char_hex_session_token",
    "username": "admin",
    "role": "admin",
    "expires_in": 86400
  }
  ```
- **Error Responses:**
  - `401 Unauthorized`: Invalid credentials.
  - `429 Too Many Requests`: Rate limit exceeded (more than 5 failed attempts in 5 minutes).

---

## 2. Telemetry & Analytics Endpoints

### `GET /api/telemetry/recent`
Retrieves recent sensor readings for a specified motor.

- **Query Parameters:**
  - `device_id` (string, optional, default: `motor01`)
  - `limit` (integer, optional, default: `100`, max: `1000`)
- **Response (200 OK):**
  ```json
  [
    {
      "id": 104,
      "event_id": "motor01-1730289600-0012",
      "device_id": "motor01",
      "timestamp": "2026-10-30T12:00:12.000Z",
      "source": "synthetic",
      "temperature_c": 38.6,
      "vibration_rms_g": 0.11,
      "current_a": 0.58,
      "rpm": 1985.0,
      "sensor_status": "ok"
    }
  ]
  ```

### `GET /api/telemetry/range`
Queries historical telemetry over an ISO-8601 time window.

- **Query Parameters:**
  - `device_id` (string, required)
  - `start_iso` (string, required, e.g. `2026-10-30T00:00:00Z`)
  - `end_iso` (string, required, e.g. `2026-10-30T23:59:59Z`)
  - `limit` (integer, optional, default: `1000`)

---

## 3. Diagnostic & Alerts Endpoints

### `GET /api/diagnosis/recent`
Returns recent hybrid rule & machine learning diagnostic verdicts.

- **Query Parameters:**
  - `device_id` (string, optional, default: `motor01`)
  - `limit` (integer, optional, default: `50`)
- **Response (200 OK):**
  ```json
  [
    {
      "id": 42,
      "event_id": "motor01-1730289600-0012",
      "device_id": "motor01",
      "timestamp": "2026-10-30T12:00:12.000Z",
      "rule_fault": "Normal",
      "rule_severity": "NORMAL",
      "ml_fault": "Normal",
      "ml_confidence": 0.985,
      "hybrid_fault": "Normal",
      "hybrid_severity": "NORMAL",
      "explanation": "Consensus reached. All operational metrics within design envelopes.",
      "recommended_action": "No intervention required.",
      "conflict_detected": 0
    }
  ]
  ```

### `GET /api/alerts`
Retrieves logged alerts from `alert_history`.

- **Query Parameters:**
  - `device_id` (string, optional)
  - `only_unacknowledged` (boolean, optional, default: `false`)
  - `limit` (integer, optional, default: `50`)

### `POST /api/alerts/{alert_id}/acknowledge`
Marks an alert as acknowledged by an operator. Requires Bearer Token authentication.

- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  {
    "status": "success",
    "alert_id": 14,
    "acknowledged_by": "operator"
  }
  ```

---

## 4. System Health & ML Metadata

### `GET /api/health`
Returns system health, MQTT broker status, SQLite accessibility, and ML model status.

- **Response (200 OK):**
  ```json
  {
    "status": "healthy",
    "environment": "development",
    "operation_mode": "simulation",
    "mqtt_broker": {
      "type": "local_fallback",
      "host": "127.0.0.1",
      "port": 1883,
      "tls": false
    },
    "database": {
      "type": "SQLite WAL",
      "accessible": true
    },
    "ml_model": {
      "loaded": true,
      "classes": ["Excessive Vibration", "Mechanical Overload", "Motor Overheating", "Motor Slowdown", "Motor Stall", "Normal", "Sensor Error"]
    }
  }
  ```

### `GET /api/ml/metrics`
Returns machine learning evaluation metrics, confusion matrix, and feature rankings.
