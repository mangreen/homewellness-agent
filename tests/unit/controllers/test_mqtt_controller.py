import io
import json
import logging

import pytest

from builders import ELDER_ID, TODAY, taipei
from homewellness.controllers.mqtt import MqttController
from homewellness.controllers.telemetry import TelemetryController
from homewellness.models.alert_policy import AlertLevel
from homewellness.models.trigger_policy import TriggerKind
from homewellness.observability import JsonFormatter
from homewellness.topics import CLOCK_TOPIC, sleep_topic, vitals_topic


class FakeClockControl:
    def __init__(self):
        self.set_to = None

    def set(self, now):
        self.set_to = now


@pytest.fixture
def received():
    return []


@pytest.fixture
def make(env, received):
    def build(clock_control=None):
        telemetry = TelemetryController(
            elders=env.elders, telemetry=env.telemetry, intakes=env.intakes,
            claims=env.claims, clock=env.clock,
        )
        return MqttController(
            telemetry=telemetry, on_trigger=lambda elder, t: received.append((elder, t)),
            clock_control=clock_control,
        )
    return build


def body(**fields) -> bytes:
    return json.dumps(fields).encode()


def critical(**changes):
    fields = {"measured_at": taipei(12, 0).isoformat(), "systolic": 188, "diastolic": 121,
              "heart_rate_bpm": 104}
    return body(**{**fields, **changes})


def should_store_vitals_and_report_a_trigger_when_a_vitals_message_arrives(make, env, received):
    env.clock.set(taipei(12, 0))
    make().handle_message(vitals_topic(ELDER_ID), critical())
    assert str(env.telemetry.latest_vitals(ELDER_ID).blood_pressure) == "188/121"
    assert [(e, t.kind, t.alert_level) for e, t in received] == [
        (ELDER_ID, TriggerKind.ABNORMAL_VITALS, AlertLevel.CRITICAL)
    ]


def should_store_sleep_and_report_a_trigger_when_a_valid_sleep_message_arrives(make, env, received):
    env.clock.set(taipei(12, 0))
    make().handle_message(
        sleep_topic(ELDER_ID), body(woke_on=TODAY.isoformat(), hours_asleep=4.5)
    )
    assert env.telemetry.latest_sleep(ELDER_ID).hours_asleep == 4.5
    assert [t.kind for _, t in received] == [TriggerKind.POOR_SLEEP]


@pytest.mark.parametrize(
    ("topic", "payload"),
    [
        (vitals_topic(ELDER_ID), b"not json"),
        (vitals_topic(ELDER_ID), critical(unexpected="field")),
        (vitals_topic(ELDER_ID), critical(measured_at="2026-10-27T12:00:00")),  # No time zone.
        (vitals_topic(ELDER_ID), critical(systolic=80, diastolic=90)),
        (vitals_topic(ELDER_ID), critical(diastolic=None)),
        (vitals_topic(ELDER_ID), body(measured_at=taipei(12, 0).isoformat())),  # No measurement.
        (vitals_topic("unknown-elder"), critical()),
        ("homewellness/e1/unknown", critical()),
    ],
)
def should_drop_the_message_when_it_is_not_acceptable(make, env, received, topic, payload):
    env.clock.set(taipei(12, 0))
    assert make().handle_message(topic, payload) == []
    assert env.telemetry.latest_vitals(ELDER_ID) is None and received == []


def should_set_the_clock_when_a_clock_message_arrives_in_demo_mode(make):
    control = FakeClockControl()
    make(control).handle_message(CLOCK_TOPIC, body(now=taipei(8, 5).isoformat()))
    assert control.set_to == taipei(8, 5)


def should_ignore_the_clock_message_when_demo_mode_is_off(make, env):
    before = env.clock.now()
    make(None).handle_message(CLOCK_TOPIC, body(now=taipei(9, 0).isoformat()))
    assert env.clock.now() == before


def should_log_one_trace_id_and_the_user_id_when_a_message_is_handled(make, env):
    env.clock.set(taipei(12, 0))
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("homewellness.mqtt")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        make().handle_message(vitals_topic(ELDER_ID), critical())
    finally:
        logger.removeHandler(handler)
    entries = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert len(entries) >= 2
    assert len({e["trace_id"] for e in entries}) == 1 and entries[0]["trace_id"] != "-"
    assert {e["user_id"] for e in entries} == {ELDER_ID}
