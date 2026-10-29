"""Production entry point: `uvicorn homewellness.main:create_production_app --factory`."""

from fastapi import FastAPI

from homewellness.api.app import create_app
from homewellness.bootstrap import build_container
from homewellness.observability import configure_logging
from homewellness.services.mqtt import MqttPublisher, MqttSubscriber
from homewellness.settings import Settings
from homewellness.topics import subscriptions


def create_production_app() -> FastAPI:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    container = build_container(settings)
    subscriber = MqttSubscriber(
        settings.mqtt_host, settings.mqtt_port, subscriptions(settings.demo_mode),
        container.mqtt.handle_message,
    )
    # NOTE: Only demo mode may publish scenarios. Run one worker process: the clock,
    # the alert list and the subscriber live in this process.
    publisher = None
    if settings.demo_mode:
        publisher = MqttPublisher(settings.mqtt_host, settings.mqtt_port)
    return create_app(container, subscriber=subscriber, publisher=publisher)
