"""
Robust MQTT Client Wrapper supporting Local Broker & HiveMQ Cloud with TLS.
Compatible with Paho MQTT 2.x and Apple Silicon.
"""

import ssl
import time
import json
import logging
from typing import Callable, Optional, Dict, Any
import certifi
import paho.mqtt.client as mqtt

logger = logging.getLogger("mqtt_client")


class ManagedMQTTClient:
    """
    Manages MQTT connection lifecycle, TLS setup, auto-reconnect, and message dispatch.
    Seamlessly falls back to local broker if cloud credentials are absent.
    """

    def __init__(
        self,
        client_id: str,
        config: Dict[str, Any],
        on_message_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        self.client_id = client_id
        self.config = config
        self.on_message_callback = on_message_callback
        self.is_connected = False
        self.last_connect_time: Optional[float] = None
        self.last_latency_ms: float = 0.0
        self.reconnect_attempts = 0

        # Initialize Paho Client with modern CallbackAPIVersion
        try:
            self.client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=self.client_id,
            )
        except AttributeError:
            self.client = mqtt.Client(client_id=self.client_id)

        self._configure_auth_and_tls()
        self._bind_callbacks()

    def _configure_auth_and_tls(self) -> None:
        username = self.config.get("username")
        password = self.config.get("password")
        if username and password:
            self.client.username_pw_set(username, password)

        if self.config.get("use_tls", False):
            context = ssl.create_default_context(cafile=certifi.where())
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            self.client.tls_set_context(context)
            logger.info("TLS 1.2/1.3 enabled with certifi CA bundle for %s", self.config.get("host"))

    def _bind_callbacks(self) -> None:
        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0 or (hasattr(rc, "is_failure") and not rc.is_failure):
                self.is_connected = True
                self.reconnect_attempts = 0
                self.last_connect_time = time.time()
                logger.info("MQTT Client '%s' successfully connected to %s:%s",
                            self.client_id, self.config.get("host"), self.config.get("port"))
            else:
                self.is_connected = False
                logger.warning("MQTT connection failed with code: %s", rc)

        def on_disconnect(client, userdata, disconnect_flags, rc=None, properties=None):
            self.is_connected = False
            logger.warning("MQTT Client '%s' disconnected (code: %s)", self.client_id, rc)

        def on_message(client, userdata, msg):
            try:
                payload_str = msg.payload.decode("utf-8")
                payload_json = json.loads(payload_str)
                if self.on_message_callback:
                    self.on_message_callback(msg.topic, payload_json)
            except Exception as exc:
                logger.error("Error decoding MQTT message on topic %s: %s", msg.topic, exc)

        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect
        self.client.on_message = on_message

    def connect(self, timeout: int = 5) -> bool:
        host = self.config.get("host", "127.0.0.1")
        port = int(self.config.get("port", 1883))
        try:
            t0 = time.time()
            self.client.connect(host, port, keepalive=60)
            self.client.loop_start()
            # Wait for connection flag with backoff
            elapsed = 0.0
            while not self.is_connected and elapsed < timeout:
                time.sleep(0.1)
                elapsed += 0.1
            if self.is_connected:
                self.last_latency_ms = round((time.time() - t0) * 1000.0, 2)
                return True
            else:
                logger.warning("MQTT connect timed out after %s seconds on %s:%s", timeout, host, port)
                return False
        except Exception as exc:
            logger.error("Failed to connect to MQTT broker %s:%s - %s", host, port, exc)
            self.is_connected = False
            return False

    def subscribe(self, topic: str, qos: int = 1) -> None:
        if self.is_connected:
            self.client.subscribe(topic, qos=qos)
            logger.info("Subscribed to topic: %s", topic)
        else:
            logger.warning("Cannot subscribe to %s: client is not connected", topic)

    def publish(self, topic: str, payload: Dict[str, Any], qos: int = 1, retain: bool = False) -> bool:
        if not self.is_connected:
            return False
        try:
            msg_str = json.dumps(payload)
            info = self.client.publish(topic, msg_str, qos=qos, retain=retain)
            return info.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as exc:
            logger.error("MQTT Publish error on topic %s: %s", topic, exc)
            return False

    def disconnect(self) -> None:
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
            logger.info("MQTT Client '%s' disconnected cleanly", self.client_id)
        except Exception as exc:
            logger.error("Error during MQTT disconnect: %s", exc)

