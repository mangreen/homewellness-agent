import pytest

from builders import ELDER_ID, make_sleep, make_vitals, taipei
from homewellness.application.handle_elder_message import HISTORY_LIMIT, HandleElderMessage
from homewellness.application.models import Role
from homewellness.domain.alert_policy import AlertLevel
from homewellness.domain.errors import EmptyMessageError
from homewellness.domain.medication import DoseState


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
    return HandleElderMessage(
        elders=env.elders, telemetry=env.telemetry, intakes=env.intakes,
        conversations=env.conversations, agent=agent, clock=env.clock,
    )


def should_pass_health_context_to_the_agent_when_the_elder_sends_a_message(use_case, env, agent):
    env.telemetry.save_vitals(make_vitals(taipei(8, 0), 158, 98))
    env.telemetry.save_sleep(make_sleep(4.5))
    use_case.execute(ELDER_ID, "我今天頭有點暈")
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
    use_case.execute(ELDER_ID, "hello")
    assert (agent.requests[0].context.vitals, agent.requests[0].context.alert_level) == (None, None)


def should_return_the_agent_reply_and_store_both_turns(use_case, env):
    reply = use_case.execute(ELDER_ID, "  吃了  ")
    turns = env.conversations.recent(ELDER_ID, 10)
    assert reply == "reply-1"
    assert [(t.role, t.text) for t in turns] == [(Role.ELDER, "吃了"), (Role.AGENT, "reply-1")]


def should_pass_recent_history_to_the_agent_when_a_second_message_arrives(use_case, agent):
    use_case.execute(ELDER_ID, "first")
    use_case.execute(ELDER_ID, "second")
    assert [t.text for t in agent.requests[1].history] == ["first", "reply-1"]


def should_limit_history_when_the_conversation_is_long(use_case, agent):
    for index in range(HISTORY_LIMIT):
        use_case.execute(ELDER_ID, f"message-{index}")
    assert len(agent.requests[-1].history) == HISTORY_LIMIT


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def should_raise_empty_message_error_when_the_text_is_blank(use_case, text):
    with pytest.raises(EmptyMessageError):
        use_case.execute(ELDER_ID, text)


def should_not_store_turns_when_the_agent_fails(use_case, env, agent):
    agent.fail = True
    with pytest.raises(RuntimeError):
        use_case.execute(ELDER_ID, "hello")
    assert env.conversations.recent(ELDER_ID, 10) == []


def should_leave_old_sleep_out_of_the_context_when_it_is_from_a_previous_day(
    use_case, env, agent
):
    from datetime import date

    env.telemetry.save_sleep(make_sleep(4.0, woke_on=date(2026, 10, 26)))
    use_case.execute(ELDER_ID, "hello")
    assert agent.requests[0].context.sleep is None
