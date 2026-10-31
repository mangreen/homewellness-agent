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


def fresh_demo_container():
    return build_container(
        Settings(store_backend="memory", demo_mode=True), clock=FixedClock(taipei(15, 0))
    )


def should_log_the_story_as_activity_events_when_scenarios_and_chat_run():
    container = fresh_demo_container()
    play(container, "morning")
    play(container, "dizzy")
    container.chat.reply(DEMO_ELDER_ID, "我今天頭有點暈")
    events = container.activity.recent(50)
    assert {e.kind for e in events} == {"clock", "device", "trigger", "tool", "alert"}
    texts = [e.text for e in events]
    for expected in ("（Demo）時間設為 08:05", "裝置回報：睡眠 4.5 小時", "主動觸發：該吃藥",
                     "主動觸發：睡眠不足", "Agent 呼叫工具：get_latest_vitals"):
        assert expected in texts
    assert any(t.startswith("警報 notify_family → family") for t in texts)


def should_forget_everything_and_allow_a_replay_when_the_container_is_reset():
    container = fresh_demo_container()
    play(container, "morning")
    container.chat.reply(DEMO_ELDER_ID, "吃了")
    container.reset()
    assert container.chat.history(DEMO_ELDER_ID, 10) == []
    assert (list(container.triggers), container.activity.recent(10)) == ([], [])
    assert container.notifier.list_sent() == []
    assert container.clock.now() == taipei(15, 0)
    play(container, "morning")  # The claims are gone, so the greeting comes again.
    assert len(container.chat.history(DEMO_ELDER_ID, 10)) == 1


def should_describe_the_offline_brain_when_the_provider_is_fake():
    brain = build_container(Settings(store_backend="memory")).brain
    assert (brain.provider, brain.model, brain.external, brain.fallback) == (
        "fake", "scripted", False, False)


def should_describe_an_external_brain_with_a_fallback_when_a_real_provider_is_set():
    settings = Settings(store_backend="memory", llm_provider="openrouter", openrouter_api_key="k")
    brain = build_container(settings).brain
    assert (brain.provider, brain.model, brain.external, brain.fallback) == (
        "openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free", True, True)


def should_not_use_a_fallback_when_it_is_switched_off():
    settings = Settings(store_backend="memory", llm_provider="anthropic", anthropic_api_key="k",
                        llm_fallback=False)
    assert build_container(settings).brain.fallback is False


def should_stop_at_start_up_when_the_key_of_the_provider_is_missing():
    import pytest

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        build_container(Settings(store_backend="memory", llm_provider="openai"))


def should_answer_with_the_offline_model_and_log_it_when_the_real_provider_cannot_be_reached():
    settings = Settings(
        store_backend="memory", demo_mode=True, llm_provider="openrouter", openrouter_api_key="k",
        openrouter_base_url="http://127.0.0.1:9/v1", llm_timeout_seconds=2.0,
    )
    container = build_container(settings, clock=FixedClock(taipei(15, 0)))
    reply = container.chat.reply(DEMO_ELDER_ID, "你好")
    assert "王奶奶" in reply  # The scripted model answered.
    events = [e.text for e in container.activity.recent(10) if e.kind == "llm"]
    assert len(events) == 1 and "改用離線模型" in events[0] and "ConnectionError" in events[0]
