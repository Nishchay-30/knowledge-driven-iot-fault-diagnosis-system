"""
MQTT Publisher Service for Synthetic DC Motor Telemetry
Publishes normalized sensor data, ground truth labels, and device heartbeats.
"""

import sys
import time
import signal
import argparse
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from simulation.scenarios import MotorScenario
from simulation.synthetic_generator import SyntheticGenerator
from ingestion.mqtt_client import ManagedMQTTClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mqtt_publisher")


class MotorMQTTPublisher:
    """
    Simulates and publishes motor telemetry via MQTT to either local Mosquitto or HiveMQ Cloud.
    """

    def __init__(
        self,
        device_id: str = "motor01",
        scenario: MotorScenario = MotorScenario.NORMAL,
        publish_interval: float = 1.0,
        seed: int = 42,
    ):
        self.device_id = device_id
        self.publish_interval = publish_interval
        self.generator = SyntheticGenerator(device_id=device_id, seed=seed)
        self.generator.set_scenario(scenario)
        self.running = False

        # Load effective MQTT config
        self.mqtt_config = settings.get_effective_mqtt_config()
        self.client = ManagedMQTTClient(
            client_id=f"sim_publisher_{device_id}_{int(time.time())}",
            config=self.mqtt_config,
            on_message_callback=self._handle_command,
        )

        self.sensor_topic = settings.get_sensor_topic(device_id)
        self.status_topic = settings.get_status_topic(device_id)
        self.ground_truth_topic = settings.get_ground_truth_topic(device_id)
        self.commands_topic = settings.get_commands_topic(device_id)

    def _handle_command(self, topic: str, payload: dict) -> None:
        """Processes remote commands sent on iot/factory/motor01/commands."""
        cmd = payload.get("command")
        logger.info("Received remote command on %s: %s", topic, cmd)
        if cmd == "set_scenario":
            scen_name = payload.get("scenario")
            try:
                self.generator.set_scenario(MotorScenario(scen_name))
                logger.info("Switched simulation scenario to: %s", scen_name)
            except Exception as exc:
                logger.error("Failed to set scenario '%s': %s", scen_name, exc)
        elif cmd == "stop":
            self.stop()

    def start(self, duration: int = 0) -> None:
        """
        Starts the publishing loop.
        duration: 0 runs indefinitely until SIGINT. >0 runs for N seconds.
        """
        logger.info("Connecting to MQTT (%s at %s:%s)...",
                    self.mqtt_config["broker_type"], self.mqtt_config["host"], self.mqtt_config["port"])
        if not self.client.connect(timeout=6):
            logger.warning("Could not establish initial MQTT connection. Will retry in loop...")

        # Subscribe to commands
        self.client.subscribe(self.commands_topic)
        self.running = True
        start_time = time.time()
        sample_count = 0

        logger.info("Simulation Publisher started for device '%s' (Scenario: %s)",
                    self.device_id, self.generator.current_scenario.value)

        try:
            while self.running:
                now = time.time()
                if duration > 0 and (now - start_time) >= duration:
                    logger.info("Completed configured simulation duration of %s seconds.", duration)
                    break

                sensor_data, ground_truth = self.generator.generate_next_sample()

                if sensor_data:
                    # Publish normalized sensor telemetry
                    self.client.publish(self.sensor_topic, sensor_data)
                    sample_count += 1
                    if sample_count % 5 == 0:
                        logger.info("Published #%s: T=%.1f°C | V=%.3fg | I=%.3fA | RPM=%.0f",
                                    sample_count,
                                    sensor_data["temperature_c"],
                                    sensor_data["vibration_rms_g"],
                                    sensor_data["current_a"],
                                    sensor_data["rpm"])

                # Always publish ground truth (separated from sensor reading)
                self.client.publish(self.ground_truth_topic, ground_truth)

                # Periodic heartbeat on status topic every 5 seconds
                if sample_count % 5 == 0:
                    status_payload = {
                        "device_id": self.device_id,
                        "uptime_seconds": int(now - start_time),
                        "status": "online" if sensor_data else "disconnected",
                        "broker": self.mqtt_config["broker_type"],
                        "timestamp": ground_truth["timestamp"],
                    }
                    self.client.publish(self.status_topic, status_payload)

                time.sleep(self.publish_interval)

        except KeyboardInterrupt:
            logger.info("Publisher stopped by keyboard interrupt.")
        finally:
            self.stop()

    def stop(self) -> None:
        self.running = False
        self.client.disconnect()
        logger.info("Publisher cleanly terminated.")


def main():
    parser = argparse.ArgumentParser(description="Synthetic Motor Telemetry MQTT Publisher")
    parser.add_argument("--device-id", default="motor01", help="Device ID")
    parser.add_argument("--scenario", default="normal",
                        choices=[s.value for s in MotorScenario], help="Motor scenario")
    parser.add_argument("--interval", type=float, default=1.0, help="Publish interval in seconds")
    parser.add_argument("--duration", type=int, default=0, help="Duration in seconds (0 = infinite)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    pub = MotorMQTTPublisher(
        device_id=args.device_id,
        scenario=MotorScenario(args.scenario),
        publish_interval=args.interval,
        seed=args.seed,
    )

    def sig_handler(sig, frame):
        logger.info("Termination signal received.")
        pub.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    pub.start(duration=args.duration)


if __name__ == "__main__":
    main()

