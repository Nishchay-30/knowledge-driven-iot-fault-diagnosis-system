"""
Central MQTT Telemetry Ingestion Service.
Subscribes to motor sensor streams, validates schemas, persists to CSV & SQLite,
and runs the hybrid AI diagnostic pipeline.
"""

import sys
import time
import signal
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from ingestion.mqtt_client import ManagedMQTTClient
from ingestion.data_validator import DataValidator
from ingestion.csv_logger import CSVLogger
from database.repository import repo
from diagnosis.hybrid_engine import hybrid_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mqtt_subscriber")


class TelemetryIngestionService:
    """
    Authoritative ingestion and diagnostic consumer.
    Maintains a sliding history buffer for rate-of-change feature calculations.
    """

    def __init__(self, device_id: str = "motor01"):
        self.device_id = device_id
        self.validator = DataValidator()
        self.csv_logger = CSVLogger(settings.CSV_LOG_PATH)
        self.repo = repo
        self.engine = hybrid_engine

        # Sliding window buffer for temporal features (last 5 readings per device)
        self.history_buffer: Dict[str, List[Dict[str, Any]]] = {}

        # Alert debouncing & persistence tracking
        self.fault_counters: Dict[str, int] = {}
        self.last_alert_time: Dict[str, float] = {}
        self.consecutive_threshold = 3  # consecutive readings required
        self.alert_cooldown_sec = 15.0  # cooldown between repeat alerts

        # MQTT Client
        self.mqtt_config = settings.get_effective_mqtt_config()
        self.client = ManagedMQTTClient(
            client_id=f"ingestion_sub_{device_id}_{int(time.time())}",
            config=self.mqtt_config,
            on_message_callback=self.on_mqtt_message,
        )

        self.sensor_topic = settings.get_sensor_topic(device_id)
        self.diagnosis_topic = settings.get_diagnosis_topic(device_id)
        self.alerts_topic = settings.get_alerts_topic(device_id)
        self.running = False

    def on_mqtt_message(self, topic: str, payload: Dict[str, Any]) -> None:
        """Callback executed on every received MQTT message."""
        if not topic.endswith("/sensors"):
            return


        # ===== ESP32 HARDWARE INTEGRATION =====
        if isinstance(payload, dict) and isinstance(
            payload.get("sensors"), dict
        ):
            import hashlib
            import json
            import math
            from datetime import datetime

            sensors = payload["sensors"]

            try:
                device_id = payload["device_id"]
                timestamp = payload["timestamp"]

                datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                )

                temp = sensors["temperature_c"]
                current = sensors["current_a"]
                rpm = sensors["rpm"]

                for value in (temp, current, rpm):
                    if (
                        isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or not math.isfinite(value)
                    ):
                        raise ValueError(
                            "Missing or invalid sensor reading"
                        )

                if not (-55 <= temp <= 125):
                    raise ValueError("Invalid temperature")
                if not (0 <= current <= 30):
                    raise ValueError("Invalid current")
                if not (0 <= rpm <= 20000):
                    raise ValueError("Invalid RPM")

            except (KeyError, ValueError, TypeError) as error:
                logger.warning(
                    "ESP32 sensor validation failed: %s",
                    error
                )
                return

            event_hash = hashlib.sha256(
                json.dumps(
                    payload, sort_keys=True
                ).encode()
            ).hexdigest()[:32]

            reading = {
                "event_id": "esp32_" + event_hash,
                "device_id": device_id,
                "timestamp": timestamp,
                "source": "esp32",
                "temperature_c": float(temp),
                "vibration_rms_g": None,
                "current_a": float(current),
                "rpm": float(rpm),
                "sensor_status": "partial"
            }


            inserted = self.repo.insert_sensor_reading(reading)

            if not inserted:
                with self.repo.manager.session() as conn:
                    duplicate = conn.execute(
                        "SELECT 1 FROM sensor_readings "
                        "WHERE event_id = ? LIMIT 1",
                        (reading["event_id"],)
                    ).fetchone()

                if duplicate:
                    logger.debug(
                        "Duplicate ESP32 MQTT reading skipped: %s",
                        reading["event_id"]
                    )
                else:
                    logger.error(
                        "ESP32 reading rejected by database: %s",
                        reading["event_id"]
                    )
                return

            logger.info(
                "ESP32 SAVED TO SQLITE: "
                "Temp=%.2f C | Current=%.3f A | RPM=%.1f",
                temp, current, rpm
            )

            try:
                from diagnosis.hardware_rules import diagnose_esp32

                if not hasattr(self, "_hardware_zero_rpm_counts"):
                    self._hardware_zero_rpm_counts = {}

                if payload.get("motor_status") == "ON" and rpm <= 0:
                    zero_count = (
                        self._hardware_zero_rpm_counts.get(device_id, 0)
                        + 1
                    )
                else:
                    zero_count = 0

                self._hardware_zero_rpm_counts[device_id] = zero_count

                prediction = diagnose_esp32(
                    reading,
                    payload.get("motor_status"),
                    rpm_zero_persistent=(zero_count >= 2)
                )

                self.repo.insert_fault_prediction(prediction)
                self._evaluate_alerts(device_id, prediction, reading)

                logger.info(
                    "ESP32 RULE DIAGNOSIS: %s [%s]",
                    prediction["rule_fault"],
                    prediction["rule_severity"],
                )

            except Exception:
                logger.exception(
                    "Hardware diagnosis failed; "
                    "sensor data was still saved"
                )

            return

        # 1. Validate payload structure & deduplicate
        is_valid, err_msg = self.validator.validate_sensor_payload(payload)
        if not is_valid:
            logger.warning("Rejected invalid telemetry message on %s: %s", topic, err_msg)
            return

        dev_id = payload["device_id"]

        # 2. Layer 1 Persistence: Append to CSV
        self.csv_logger.append_reading(payload)

        # 3. Layer 3 Persistence: Authoritative SQLite storage
        inserted = self.repo.insert_sensor_reading(payload)
        if not inserted:
            logger.debug("Duplicate sensor reading skipped in DB: %s", payload["event_id"])
            return

        # Maintain sliding history buffer for temporal feature extraction
        history = self.history_buffer.setdefault(dev_id, [])
        history.append(payload)
        if len(history) > 10:
            history.pop(0)

        # 4. Layer 5 Diagnostic Engine: Evaluate Rule + ML Hybrid
        diagnosis = self.engine.diagnose(payload, history)

        # Save diagnosis to SQLite
        self.repo.insert_fault_prediction(diagnosis)

        # Publish diagnostic verdict back to MQTT
        self.client.publish(self.diagnosis_topic, diagnosis)

        # 5. Layer 4 Automation & Alert Evaluation
        self._evaluate_alerts(dev_id, diagnosis, payload)

    def _evaluate_alerts(self, dev_id: str, diagnosis: Dict[str, Any], raw_reading: Dict[str, Any]) -> None:
        """Evaluates consecutive persistence and alert cooldown."""
        sev = diagnosis["hybrid_severity"]
        fault = diagnosis["hybrid_fault"]
        now = time.time()

        # For ESP32 hardware, count consecutive readings
        # only when they report the SAME fault.
        if raw_reading.get("source") == "esp32":
            if not hasattr(self, "_hardware_previous_faults"):
                self._hardware_previous_faults = {}

            previous_fault = self._hardware_previous_faults.get(
                dev_id
            )

            if previous_fault != fault:
                self.fault_counters[dev_id] = 0

            self._hardware_previous_faults[dev_id] = fault

        if sev == "NORMAL":
            # Clear counter when healthy
            self.fault_counters[dev_id] = 0
            return

        # Increment consecutive counter for persistent conditions
        self.fault_counters[dev_id] = self.fault_counters.get(dev_id, 0) + 1
        count = self.fault_counters[dev_id]

        # Trigger alert if consecutive threshold is met or if severity is CRITICAL
        is_critical = sev in ("CRITICAL", "UNKNOWN / SENSOR ERROR")
        last_alert = self.last_alert_time.get(dev_id, 0.0)
        cooldown_elapsed = (now - last_alert) >= self.alert_cooldown_sec

        is_hardware = raw_reading.get("source") == "esp32"

        if is_hardware:
            # Critical faults alert immediately.
            # Missing speed feedback already requires
            # two consecutive zero-RPM measurements.
            # Other warnings require two abnormal diagnoses.
            should_alert = (
                is_critical
                or fault == "Speed Feedback Missing"
                or count >= 2
            )
        else:
            should_alert = (
                count >= self.consecutive_threshold
                or is_critical
            )

        if should_alert and cooldown_elapsed:
            self.last_alert_time[dev_id] = now
            title = f"{sev}: {fault} on {dev_id}"
            message = (
                f"Diagnostic Alert: {fault} (Severity: {sev}). "
                f"Confidence: {diagnosis.get('hybrid_confidence', 0.0)*100:.1f}%. "
                f"T={raw_reading['temperature_c']}°C, V={raw_reading['vibration_rms_g']}g, "
                f"I={raw_reading['current_a']}A, RPM={raw_reading['rpm']}. "
                f"Action: {diagnosis.get('recommended_action')}"
            )

            if is_hardware:
                message = (
                    f"Hardware Alert: {fault} "
                    f"(Severity: {sev}). "
                    f"Temperature={raw_reading['temperature_c']} C, "
                    f"Current={raw_reading['current_a']} A, "
                    f"RPM={raw_reading['rpm']}. "
                    f"Vibration not measured. "
                    f"ML diagnosis not evaluated. "
                    f"Action: {diagnosis.get('recommended_action')}"
                )

            # Record in SQLite alert history
            alert_id = self.repo.insert_alert(
                device_id=dev_id,
                severity=sev,
                title=title,
                message=message,
                timestamp=raw_reading["timestamp"],
            )

            # Publish actionable alert to MQTT (for Node-RED / ESP32 buzzer/LED)
            alert_payload = {
                "alert_id": alert_id,
                "device_id": dev_id,
                "timestamp": raw_reading["timestamp"],
                "severity": sev,
                "fault": fault,
                "title": title,
                "message": message,
                "recommended_action": diagnosis.get("recommended_action"),
                "actuate_hardware": is_critical and not is_hardware,  # flag for ESP32 buzzer/LED
            }
            self.client.publish(self.alerts_topic, alert_payload)
            logger.warning("🚨 [ALERT DISPATCHED] %s (ID: %s)", title, alert_id)

    def start(self) -> None:
        """Starts subscriber connection and message loop."""
        logger.info("Connecting Ingestion Service to MQTT (%s at %s:%s)...",
                    self.mqtt_config["broker_type"], self.mqtt_config["host"], self.mqtt_config["port"])
        if not self.client.connect(timeout=6):
            logger.warning("MQTT broker connection could not be established immediately. Waiting in loop...")

        # Subscribe to all sensor topics
        wildcard_topic = "iot/factory/+/sensors"
        self.client.subscribe(wildcard_topic)
        self.running = True
        logger.info("Telemetry Ingestion Service listening on '%s'", wildcard_topic)

        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("Ingestion Service stopped by user.")
        finally:
            self.stop()

    def stop(self) -> None:
        self.running = False
        self.client.disconnect()
        logger.info("Ingestion Service stopped.")


def main():
    service = TelemetryIngestionService()

    def sig_handler(sig, frame):
        service.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    service.start()


if __name__ == "__main__":
    main()

