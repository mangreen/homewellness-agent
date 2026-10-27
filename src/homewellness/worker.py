"""Worker process: listens to device messages on MQTT and runs the telemetry controller."""

import logging
import signal
import threading

from homewellness.bootstrap import build_container
from homewellness.health import start_health_server
from homewellness.observability import configure_logging
from homewellness.services.mqtt import MqttSubscriber
from homewellness.settings import Settings
from homewellness.topics import subscriptions

logger = logging.getLogger("homewellness.worker")


def main() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    container = build_container(settings)
    subscriber = MqttSubscriber(
        settings.mqtt_host, settings.mqtt_port, subscriptions(settings.demo_mode),
        container.mqtt.handle_message,
    )
    # Healthy means: connected to the broker and subscribed.
    health = start_health_server(settings.health_port, subscriber.is_ready)
    subscriber.start()
    logger.info("worker started", extra={
        "event": "worker_started", "demo_mode": settings.demo_mode, "store": settings.store_backend,
    })

    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    stop.wait()
    subscriber.stop()
    health.shutdown()


if __name__ == "__main__":
    main()
