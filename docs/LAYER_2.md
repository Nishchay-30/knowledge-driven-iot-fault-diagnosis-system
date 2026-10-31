# Layer 2 — Cloud MQTT Integration (HiveMQ Cloud TLS) with Local Fallback

## 1. Objective
Upgrade the communication pipeline from local unencrypted MQTT to production-grade cloud messaging using **HiveMQ Cloud** with TLS v1.2/1.3 encryption (Port 8883) and username/password authentication, while ensuring automatic, graceful fallback to a local broker during offline or credentials-free operation.

---

## 2. Key Architecture & Features

### A. Managed MQTT Client (`ingestion/mqtt_client.py`)
- **Transport Security**: Wraps sockets in TLS using standard system CA certificates when connecting to port 8883.
- **Resilient Reconnection**: Implements exponential backoff ($1\,\text{s} \to 2\,\text{s} \to 4\,\text{s} \to \dots \to 30\,\text{s}$) to gracefully handle network drops.
- **Connection Health & Latency**: Measures round-trip ping times and logs broker disconnect reasons.
- **Offline / Local Broker Fallback**: If HiveMQ Cloud credentials are unconfigured or connection times out, the client automatically switches to local Mosquitto (`127.0.0.1:1883`), preventing unhandled crashes.

### B. Environment Configuration (`config/settings.py` & `.env.example`)
All credentials are decoupled from source code:
```env
# MQTT Mode: set USE_LOCAL_BROKER=false to enable HiveMQ Cloud
USE_LOCAL_BROKER=true
LOCAL_MQTT_HOST=127.0.0.1
LOCAL_MQTT_PORT=1883

# HiveMQ Cloud Credentials (Port 8883 with TLS)
HIVEMQ_HOST=xxxxxx.s1.eu.hivemq.cloud
HIVEMQ_PORT=8883
HIVEMQ_USERNAME=your_username
HIVEMQ_PASSWORD=your_secure_password
HIVEMQ_USE_TLS=true
```

---

## 3. Verification & Execution
To verify Layer 2 connectivity and fallback:
```bash
./scripts/run_layer2.sh
```
Or run the MQTT test suite:
```bash
./.venv/bin/pytest tests/test_mqtt.py -v
```
