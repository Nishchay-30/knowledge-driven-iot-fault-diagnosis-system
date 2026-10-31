# Node-RED Industrial Automation & Alert Flow

This directory contains the production Node-RED workflow orchestrating telemetry parsing, validation, debounce hysteresis, and alert dispatch for the **Knowledge-Driven IoT-Based Fault Diagnosis System**.

---

## 1. Flow Capabilities

The flow in `flows.json` provides:
1. **MQTT Telemetry Subscription**: Listens to wildcard topic `iot/factory/+/sensors`.
2. **Payload Parsing & Deduplication**: Parses JSON and drops duplicate readings by caching recent `event_id` tokens.
3. **Multi-Condition Alert Evaluation**:
   - **Motor Stall / Locked Rotor**: $I \ge 1.70\,\text{A} \land \text{RPM} \le 250$ $\to$ `CRITICAL`
   - **Motor Overheating**: $T \ge 65.0^\circ\text{C} \land I \ge 0.90\,\text{A}$ $\to$ `CRITICAL`
   - **Sensor Out-of-Range**: $T < -20^\circ\text{C} \lor T > 120^\circ\text{C} \lor I < 0 \lor \text{RPM} < 0$ $\to$ `UNKNOWN / SENSOR ERROR`
   - **Mechanical Overload**: $I \ge 1.05\,\text{A} \land \text{RPM} < 1600$ $\to$ `WARNING`
   - **Excessive Vibration**: $\text{RMS} \ge 0.40\,g$ $\to$ `WARNING`
4. **Hysteresis & Cooldown Suppression**:
   - Requires **3 consecutive anomalous readings** before firing a persistent alert (unless severity is `CRITICAL`).
   - Enforces a **15-second alert cooldown** to prevent message flooding.
5. **Recovery Notification**: Dispatches an automatic recovery message when telemetry returns to nominal thresholds after an active fault state.
6. **MQTT Alert Publishing**: Dispatches actionable alert events to `iot/factory/motor01/alerts`.

---

## 2. Launching Node-RED on Apple Silicon Mac

### Option A: Using Docker Compose (Recommended)
From the project root:
```bash
docker compose up nodered -d
```
Node-RED will be available at: `http://localhost:1880`.

### Option B: Running Node-RED Locally via npm
```bash
cd nodered
npm install
npx node-red --userDir . flows.json
```

---

## 3. Importing the Flow Manually
If running an existing Node-RED instance:
1. Open `http://localhost:1880` in your browser.
2. Click the top-right hamburger menu $\to$ **Import**.
3. Select `nodered/flows.json` or paste its contents.
4. Click **Import** $\to$ **Deploy**.
5. Check the MQTT broker node configuration:
   - For local Mosquitto: `127.0.0.1:1883`
   - For HiveMQ Cloud: Host `xxxxxx.s1.eu.hivemq.cloud`, Port `8883`, TLS enabled, with your HiveMQ credentials.
