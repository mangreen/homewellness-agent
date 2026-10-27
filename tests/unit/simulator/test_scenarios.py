import json
from types import SimpleNamespace

import pytest

from builders import TODAY, taipei
from homewellness.controllers.mqtt import MqttController
from homewellness.controllers.telemetry import TelemetryController
from homewellness.demo import DEMO_ELDER_ID, demo_profile
from homewellness.models.alert_policy import AlertLevel
from homewellness.models.trigger_policy import TriggerKind
from homewellness.services.clock import FixedClock, SimulatedClock
from homewellness.simulator.scenarios import SCENARIO_NAMES, build_scenario
from homewellness.stores.memory import (
    InMemoryClaimStore,
    InMemoryElderStore,
    InMemoryIntakeStore,
    InMemoryTelemetryStore,
)
from homewellness.topics import CLOCK_TOPIC


@pytest.fixture
def pipeline():
    """The demo pipeline without the network. The clock starts in the afternoon."""
    clock = SimulatedClock(FixedClock(taipei(15, 0)))
    triggers = []
    telemetry = TelemetryController(
        elders=InMemoryElderStore([demo_profile()]), telemetry=InMemoryTelemetryStore(),
        intakes=InMemoryIntakeStore(), claims=InMemoryClaimStore(), clock=clock,
    )
    controller = MqttController(
        telemetry=telemetry, on_trigger=lambda elder, t: triggers.append(t), clock_control=clock
    )

    def play(name):
        for message in build_scenario(name, DEMO_ELDER_ID, TODAY):
            controller.handle_message(message.topic, message.body())

    return SimpleNamespace(play=play, triggers=triggers)


def should_list_the_three_demo_scenarios():
    assert SCENARIO_NAMES == ("morning", "dizzy", "crisis")


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def should_move_the_clock_before_any_telemetry_when_a_scenario_starts(name):
    messages = build_scenario(name, DEMO_ELDER_ID, TODAY)
    assert messages[0].topic == CLOCK_TOPIC
    assert all(m.topic != CLOCK_TOPIC for m in messages[1:])


def should_raise_value_error_when_the_scenario_name_is_unknown():
    with pytest.raises(ValueError, match="morning"):
        build_scenario("nope", DEMO_ELDER_ID, TODAY)


def should_encode_the_message_body_as_json_bytes():
    message = build_scenario("crisis", DEMO_ELDER_ID, TODAY)[1]
    assert json.loads(message.body())["systolic"] == 188


def should_greet_about_medicine_and_sleep_when_the_morning_scenario_runs(pipeline):
    pipeline.play("morning")
    assert [t.kind for t in pipeline.triggers] == [
        TriggerKind.MEDICATION_DUE, TriggerKind.POOR_SLEEP,
    ]
    assert pipeline.triggers[1].sleep_hours == 4.5


def should_raise_no_proactive_trigger_when_the_dizzy_scenario_runs_after_morning(pipeline):
    pipeline.play("morning")
    before = len(pipeline.triggers)
    pipeline.play("dizzy")
    assert len(pipeline.triggers) == before


def should_raise_a_critical_trigger_when_the_crisis_scenario_runs_after_dizzy(pipeline):
    pipeline.play("morning")
    pipeline.play("dizzy")
    pipeline.play("crisis")
    last = pipeline.triggers[-1]
    assert (last.kind, last.alert_level) == (TriggerKind.ABNORMAL_VITALS, AlertLevel.CRITICAL)
    assert str(last.blood_pressure) == "188/121"


def should_use_the_demo_elder_profile_with_two_daily_doses():
    profile = demo_profile()
    assert profile.elder_id == DEMO_ELDER_ID
    assert [d.dose_id for d in profile.medication_schedule.doses] == ["am", "pm"]
