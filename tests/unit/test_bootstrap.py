from builders import TODAY, taipei
from homewellness.bootstrap import build_container
from homewellness.demo import DEMO_ELDER_ID
from homewellness.models.trigger_policy import TriggerKind
from homewellness.services.clock import FixedClock, SimulatedClock
from homewellness.settings import Settings
from homewellness.simulator.scenarios import build_scenario


def play(container, name):
    for message in build_scenario(name, DEMO_ELDER_ID, TODAY):
        container.mqtt.handle_message(message.topic, message.body())


def should_record_triggers_when_the_morning_scenario_runs_in_demo_mode():
    container = build_container(
        Settings(store_backend="memory", demo_mode=True), clock=FixedClock(taipei(15, 0))
    )
    play(container, "morning")
    assert isinstance(container.clock, SimulatedClock)
    assert [t.kind for _, t in container.triggers] == [
        TriggerKind.MEDICATION_DUE, TriggerKind.POOR_SLEEP,
    ]


def should_ignore_clock_messages_when_demo_mode_is_off():
    container = build_container(
        Settings(store_backend="memory", demo_mode=False), clock=FixedClock(taipei(15, 0))
    )
    play(container, "crisis")  # The clock stays real, so the reading is stale.
    assert list(container.triggers) == []


def should_keep_only_the_newest_triggers_when_many_arrive():
    container = build_container(Settings(store_backend="memory", demo_mode=True))
    for index in range(150):
        container.record_trigger(DEMO_ELDER_ID, index)
    assert len(container.triggers) == 100
