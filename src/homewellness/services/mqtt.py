"""MQTT client wrappers (paho). Mosquitto stands in for AWS IoT Core. The protocol is the same."""

import logging
import threading
import uuid
from collections.abc import Callable

import paho.mqtt.client as mqtt

logger = logging.getLogger("homewellness.mqtt")


def _client(prefix: str) -> mqtt.Client:
    client_id = f"{prefix}-{uuid.uuid4().hex[:8]}"
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)


class MqttPublisher:
    def __init__(self, host: str, port: int) -> None:
        self._client = _client("hw-pub")
        self._client.connect(host, port, keepalive=30)
        self._client.loop_start()

    def publish(self, topic: str, body: bytes) -> None:
        info = self._client.publish(topic, body, qos=1)
        info.wait_for_publish(timeout=5)
        if not info.is_published():
            raise TimeoutError(f"message to {topic} was not confirmed by the broker")

    def close(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()


class MqttSubscriber:
    """Subscribes to topics and calls `on_message(topic, payload)` for each message.

    NOTE: The client reconnects by itself. It subscribes again after each reconnect.
    """

    def __init__(
        self, host: str, port: int, topics: list[str], on_message: Callable[[str, bytes], None]
    ) -> None:
        self._host, self._port = host, port
        self._topics = topics
        self._on_message = on_message
        self._ready = threading.Event()
        self._client = _client("hw-sub")
        self._client.on_connect = self._handle_connect
        self._client.on_disconnect = self._handle_disconnect
        self._client.on_subscribe = lambda *_: self._ready.set()
        self._client.on_message = self._handle_message

    def start(self) -> None:
        self._client.connect_async(self._host, self._port, keepalive=30)
        self._client.loop_start()

    def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def is_ready(self) -> bool:
        return self._ready.is_set()

    def wait_until_ready(self, timeout: float) -> bool:
        return self._ready.wait(timeout)

    def _handle_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code.is_failure:
            logger.error("mqtt connect failed", extra={"event": "mqtt_connect_failed"})
            return
        client.subscribe([(topic, 1) for topic in self._topics])
        logger.info("mqtt connected", extra={"event": "mqtt_connected"})

    def _handle_disconnect(self, client, userdata, flags, reason_code, properties) -> None:
        self._ready.clear()
        logger.warning("mqtt disconnected", extra={"event": "mqtt_disconnected"})

    def _handle_message(self, client, userdata, message) -> None:
        try:
            self._on_message(message.topic, message.payload)
        except Exception:  # noqa: BLE001 - one bad message must not stop the loop
            logger.exception("message handler failed", extra={"event": "handler_failed"})
