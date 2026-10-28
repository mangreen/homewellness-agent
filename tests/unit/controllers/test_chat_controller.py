import pytest

from builders import ELDER_ID, make_sleep, make_vitals, taipei
from homewellness.controllers.chat import HISTORY_LIMIT, ChatController
from homewellness.models.alert_policy import AlertLevel
from homewellness.models.errors import EmptyMessageError
from homewellness.models.interaction import Role
from homewellness.models.medication import DoseState


class FakeAgent:
    """Test double for the AgentRunner port."""

    def __init__(self):
        self.requests = []
        self.fail = False

    def reply(self, request):
        if self.fail:
            raise RuntimeError("agent down")
        self.requests.append(request)
        return f"reply-{len(self.requests)}"


@pytest.fixture
def agent():
    return FakeAgent()


@pytest.fixture
def use_case(env, agent):
    return ChatController(
        elders=env.elders, telemetry=env.telemetry, intakes=env.intakes,
        conversations=env.conversations, agent=agent, clock=env.clock,
    )


def should_pass_health_context_to_the_agent_when_the_elder_sends_a_message(use_case, env, agent):
    env.telemetry.save_vitals(make_vitals(taipei(8, 0), 158, 98))
    env.telemetry.save_sleep(make_sleep(4.5))
    use_case.reply(ELDER_ID, "我今天頭有點暈")
    request = agent.requests[0]
    assert request.message == "我今天頭有點暈"
    assert request.context.display_name == "王奶奶"
    assert request.context.alert_level is AlertLevel.ELEVATED
    assert request.context.sleep.hours_asleep == 4.5
    assert [(d.dose.dose_id, d.state) for d in request.context.doses] == [
        ("am", DoseState.DUE), ("pm", DoseState.UPCOMING),
    ]


def should_leave_stale_vitals_out_of_the_context_when_the_reading_is_old(use_case, env, agent):
    env.telemetry.save_vitals(make_vitals(taipei(7, 0), 158, 98))
    use_case.reply(ELDER_ID, "hello")
    assert (agent.requests[0].context.vitals, agent.requests[0].context.alert_level) == (None, None)


def should_return_the_agent_reply_and_store_both_turns(use_case, env):
    reply = use_case.reply(ELDER_ID, "  吃了  ")
    turns = env.conversations.recent(ELDER_ID, 10)
    assert reply == "reply-1"
    assert [(t.role, t.text) for t in turns] == [(Role.ELDER, "吃了"), (Role.AGENT, "reply-1")]


def should_pass_recent_history_to_the_agent_when_a_second_message_arrives(use_case, agent):
    use_case.reply(ELDER_ID, "first")
    use_case.reply(ELDER_ID, "second")
    assert [t.text for t in agent.requests[1].history] == ["first", "reply-1"]


def should_limit_history_when_the_conversation_is_long(use_case, agent):
    for index in range(HISTORY_LIMIT):
        use_case.reply(ELDER_ID, f"message-{index}")
    assert len(agent.requests[-1].history) == HISTORY_LIMIT


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def should_raise_empty_message_error_when_the_text_is_blank(use_case, text):
    with pytest.raises(EmptyMessageError):
        use_case.reply(ELDER_ID, text)


def should_not_store_turns_when_the_agent_fails(use_case, env, agent):
    agent.fail = True
    with pytest.raises(RuntimeError):
        use_case.reply(ELDER_ID, "hello")
    assert env.conversations.recent(ELDER_ID, 10) == []


def should_leave_old_sleep_out_of_the_context_when_it_is_from_a_previous_day(
    use_case, env, agent
):
    from datetime import date

    env.telemetry.save_sleep(make_sleep(4.0, woke_on=date(2026, 10, 26)))
    use_case.reply(ELDER_ID, "hello")
    assert agent.requests[0].context.sleep is None


def should_put_the_system_prompt_in_the_request_without_live_vitals(use_case, env, agent):
    env.telemetry.save_vitals(make_vitals(taipei(8, 0), 158, 98))
    use_case.reply(ELDER_ID, "hello")
    prompt = agent.requests[0].system_prompt
    assert "稱呼：王奶奶" in prompt and "158/98" not in prompt


def should_return_the_history_oldest_first_when_it_is_requested(use_case):
    use_case.reply(ELDER_ID, "first")
    use_case.reply(ELDER_ID, "second")
    assert [t.text for t in use_case.history(ELDER_ID, 10)] == [
        "first", "reply-1", "second", "reply-2"]


def should_return_the_health_context_when_the_status_is_requested(use_case):
    assert use_case.status(ELDER_ID).display_name == "王奶奶"


def trigger(kind=None):
    from datetime import time

    from homewellness.models.medication import Dose
    from homewellness.models.trigger_policy import ProactiveTrigger, TriggerKind

    dose = Dose("am", "早上", time(8))
    return ProactiveTrigger(kind or TriggerKind.MEDICATION_DUE, "k", dose=dose)


def should_send_an_event_message_to_the_agent_when_triggers_arrive(use_case, agent):
    reply = use_case.proactive(ELDER_ID, [trigger()])
    assert reply == "reply-1"
    assert agent.requests[0].message.startswith("[SYSTEM_EVENT]")
    assert "kind=medication_due" in agent.requests[0].message


def should_store_only_the_agent_turn_when_a_proactive_message_is_sent(use_case, env):
    use_case.proactive(ELDER_ID, [trigger()])
    assert [(t.role, t.text) for t in env.conversations.recent(ELDER_ID, 10)] == [
        (Role.AGENT, "reply-1")]


def should_do_nothing_when_there_are_no_triggers(use_case, agent, env):
    assert use_case.proactive(ELDER_ID, []) is None
    assert agent.requests == [] and env.conversations.recent(ELDER_ID, 10) == []
