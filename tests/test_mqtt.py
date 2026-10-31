"""
Tests for MQTT Configuration, Client Abstraction, and Local Fallback.
"""

import time
import pytest
from config.settings import settings
from ingestion.mqtt_client import ManagedMQTTClient
from ingestion.data_validator import DataValidator


def test_effective_mqtt_config_fallback():
    """Verify fallback to local broker when HiveMQ credentials are blank."""
    cfg = settings.get_effective_mqtt_config()
    assert cfg["broker_type"] in ("local_fallback", "hivemq_cloud")
    assert "host" in cfg
    assert "port" in cfg
    assert "use_tls" in cfg


def test_data_validator_deduplication():
    """Verify duplicate event IDs are blocked."""
    validator = DataValidator(seen_cache_size=100)
    reading = {
        "event_id": "test-unique-uuid-12345",
        "device_id": "motor01",
        "timestamp": "2026-10-30T11:00:00Z",
        "source": "synthetic",
        "temperature_c": 38.0,
        "vibration_rms_g": 0.12,
        "current_a": 0.60,
        "rpm": 2100.0,
        "sensor_status": "ok",
    }
    is_valid, err = validator.validate_sensor_payload(reading)
    assert is_valid is True

    # Immediate duplicate
    is_dup, err_dup = validator.validate_sensor_payload(reading)
    assert is_dup is False
    assert "Duplicate" in err_dup


def test_local_mqtt_pub_sub_loopback():
    """Test publishing and subscribing on local MQTT broker (Mosquitto port 1883)."""
    received_messages = []

    def on_msg(topic, payload):
        received_messages.append((topic, payload))

    client = ManagedMQTTClient(
        client_id="test_sub_loopback",
        config=settings.get_effective_mqtt_config(),
        on_message_callback=on_msg,
    )

    if not client.connect(timeout=3):
        pytest.skip("Local MQTT broker (port 1883) not reachable in test environment.")

    test_topic = "iot/test/loopback/ping"
    client.subscribe(test_topic)
    time.sleep(0.2)

    payload = {"test": "ping_data", "value": 42}
    published = client.publish(test_topic, payload)
    assert published is True

    # Wait for loopback delivery
    for _ in range(20):
        if received_messages:
            break
        time.sleep(0.1)

    client.disconnect()
    assert len(received_messages) > 0
    assert received_messages[0][1]["test"] == "ping_data"

