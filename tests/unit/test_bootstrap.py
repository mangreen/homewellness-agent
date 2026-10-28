from builders import TODAY, taipei
from homewellness.bootstrap import build_container
from homewellness.demo import DEMO_ELDER_ID
from homewellness.models.trigger_policy import ProactiveTrigger, TriggerKind
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
    triggers = [
        ProactiveTrigger(TriggerKind.POOR_SLEEP, f"s{i}", sleep_hours=4.0) for i in range(150)
    ]
    container.handle_triggers(DEMO_ELDER_ID, triggers)
    assert len(container.triggers) == 100


def should_store_one_proactive_greeting_when_the_morning_scenario_runs():
    container = build_container(
        Settings(store_backend="memory", demo_mode=True), clock=FixedClock(taipei(15, 0))
    )
    play(container, "morning")
    turns = container.chat.history(DEMO_ELDER_ID, 10)
    assert len(turns) == 1 and turns[0].role.value == "agent"
    assert "早安" in turns[0].text and "降血壓藥" in turns[0].text


def should_keep_ingesting_when_the_agent_fails_to_greet():
    import pytest

    from homewellness.models.errors import AgentUnavailableError

    class BrokenChat:
        def proactive(self, elder_id, triggers):
            raise AgentUnavailableError("down")

    container = build_container(
        Settings(store_backend="memory", demo_mode=True), clock=FixedClock(taipei(15, 0))
    )
    container.chat = BrokenChat()
    play(container, "morning")
    assert len(container.triggers) == 2
    del pytest


def should_raise_value_error_when_the_llm_provider_is_not_implemented():
    import pytest

    with pytest.raises(ValueError, match="gpt"):
        build_container(Settings(store_backend="memory", llm_provider="gpt"))
