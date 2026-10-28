"""The whole application over a real broker and DynamoDB: scenario -> MQTT -> agent -> API."""

import os
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from homewellness.api.app import create_app
from homewellness.bootstrap import build_container
from homewellness.services.mqtt import MqttPublisher, MqttSubscriber
from homewellness.settings import Settings
from homewellness.topics import subscriptions
from tests_support import ELDER, key

pytestmark = pytest.mark.integration


def wait_for(condition, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.1)
    return False


def should_greet_talk_and_alert_when_scenarios_cross_the_real_broker(broker, dynamo_table):
    host, port = broker
    settings = Settings(
        store_backend="dynamodb", mqtt_host=host, mqtt_port=port, demo_mode=True,
        dynamodb_endpoint=os.environ["DYNAMODB_ENDPOINT"],
        dynamodb_table=f"hw-app-{uuid.uuid4().hex[:8]}",  # A fresh table: no old claims.
    )
    container = build_container(settings)
    subscriber = MqttSubscriber(host, port, subscriptions(True), container.mqtt.handle_message)
    app = create_app(container, subscriber=subscriber, publisher=MqttPublisher(host, port))

    with TestClient(app) as client:
        def start(name):
            assert client.post(f"/sim/scenarios/{name}", headers={"Idempotency-Key": key()}
                               ).status_code == 200

        def say(text):
            response = client.post(f"/elders/{ELDER}/messages", json={"text": text},
                                   headers={"Idempotency-Key": key()})
            assert response.status_code == 200, response.text
            return response.json()["reply"]

        def status():
            return client.get(f"/elders/{ELDER}/status").json()

        assert wait_for(subscriber.is_ready) and client.get("/healthz").status_code == 200

        start("morning")  # Device data over MQTT. The agent greets first.
        assert wait_for(lambda: client.get(f"/elders/{ELDER}/conversation").json()["turns"])
        greeting = client.get(f"/elders/{ELDER}/conversation").json()["turns"][0]
        assert greeting["role"] == "agent" and "早安" in greeting["text"]
        assert "記下" in say("吃了")

        start("dizzy")
        assert wait_for(lambda: status()["blood_pressure"] == "158/98")
        reply = say("我今天頭有點暈")
        assert "158/98" in reply and "小美" in reply
        alerts = client.get("/alerts").json()["alerts"]
        assert [a["action"] for a in alerts] == ["notify_family"]
