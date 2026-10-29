"""Device message -> real Mosquitto -> subscriber -> controller -> DynamoDB."""

import json
import time
from types import SimpleNamespace

import pytest

from builders import TODAY, make_profile, taipei
from homewellness.controllers.mqtt import MqttController
from homewellness.controllers.telemetry import TelemetryController
from homewellness.models.alert_policy import AlertLevel
from homewellness.models.trigger_policy import TriggerKind
from homewellness.services.clock import FixedClock, SimulatedClock
from homewellness.services.mqtt import MqttPublisher, MqttSubscriber
from homewellness.simulator.scenarios import build_scenario
from homewellness.stores.dynamodb import stores as dynamo
from homewellness.stores.memory import InMemoryElderStore
from homewellness.topics import subscriptions, vitals_topic

pytestmark = pytest.mark.integration


def critical_payload(at) -> bytes:
    return json.dumps({"measured_at": at.isoformat(), "systolic": 188, "diastolic": 121}).encode()


def wait_for(condition, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.05)
    return False


@pytest.fixture
def pipeline(broker, dynamo_table, elder_id):
    clock = SimulatedClock(FixedClock(taipei(12, 0)))
    received = []
    telemetry = dynamo.DynamoTelemetryStore(dynamo_table)
    controller = MqttController(
        telemetry=TelemetryController(
            elders=InMemoryElderStore([make_profile(elder_id)]), telemetry=telemetry,
            intakes=dynamo.DynamoIntakeStore(dynamo_table),
            claims=dynamo.DynamoClaimStore(dynamo_table), clock=clock,
        ),
        on_triggers=lambda elder, triggers: received.extend(triggers),
        clock_control=clock,
    )
    subscriber = MqttSubscriber(*broker, subscriptions(True), controller.handle_message)
    subscriber.start()
    assert subscriber.wait_until_ready(10), "subscriber did not connect to the broker"
    publisher = MqttPublisher(*broker)
    yield SimpleNamespace(received=received, telemetry=telemetry, publisher=publisher)
    publisher.close()
    subscriber.stop()


def should_store_vitals_and_report_a_trigger_when_a_device_message_crosses_the_broker(
    pipeline, elder_id
):
    pipeline.publisher.publish(vitals_topic(elder_id), critical_payload(taipei(12, 0)))
    assert wait_for(lambda: pipeline.received), "no trigger arrived"
    assert (pipeline.received[0].kind, pipeline.received[0].alert_level) == (
        TriggerKind.ABNORMAL_VITALS, AlertLevel.CRITICAL)
    assert str(pipeline.telemetry.latest_vitals(elder_id).blood_pressure) == "188/121"


def should_play_the_morning_scenario_when_it_crosses_the_broker(pipeline, elder_id):
    for message in build_scenario("morning", elder_id, TODAY):
        pipeline.publisher.publish(message.topic, message.body())
    assert wait_for(lambda: len(pipeline.received) >= 2), "expected two triggers"
    assert [t.kind for t in pipeline.received] == [
        TriggerKind.MEDICATION_DUE, TriggerKind.POOR_SLEEP]


def should_keep_working_when_a_bad_message_crosses_the_broker(pipeline, elder_id):
    pipeline.publisher.publish(vitals_topic(elder_id), b"not json at all")
    pipeline.publisher.publish(vitals_topic(elder_id), critical_payload(taipei(12, 0)))
    assert wait_for(lambda: pipeline.received), "worker stopped after a bad message"
