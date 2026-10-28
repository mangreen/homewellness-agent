import uuid

import pytest
from langchain_core.messages import AIMessage

from builders import make_health_context
from homewellness.models.errors import AgentUnavailableError
from homewellness.models.interaction import AgentRequest, ConversationTurn, Role
from homewellness.services.agent import LangChainAgentRunner
from homewellness.services.scripted_model import ScriptedChatModel
from tests_support import FakeActions

SYSTEM = "稱呼：王奶奶\n家屬：小美\n現在時間：08:05\n"


def request(message="我今天頭有點暈", elder_id="e-1", history=()):
    return AgentRequest(elder_id, message, make_health_context(elder_id), tuple(history), SYSTEM)


def should_read_vitals_ask_the_policy_and_answer_when_the_elder_is_dizzy():
    actions = FakeActions()
    reply = LangChainAgentRunner(ScriptedChatModel(), actions).reply(request())
    assert "158/98" in reply
    assert actions.calls == [("get_latest_vitals", "e-1"),
                             ("escalate_emergency", "e-1", ["dizziness"])]


def should_bind_every_tool_call_to_the_elder_of_the_request():
    actions = FakeActions()
    LangChainAgentRunner(ScriptedChatModel(), actions).reply(request(elder_id="e-42"))
    assert {call[1] for call in actions.calls} == {"e-42"}


def should_send_the_history_and_the_system_prompt_to_the_model():
    seen = []

    class Spy(ScriptedChatModel):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            seen.append(messages)
            return super()._generate(messages, stop, run_manager, **kwargs)

    history = [ConversationTurn(Role.ELDER, "早", None), ConversationTurn(Role.AGENT, "早安", None)]
    LangChainAgentRunner(Spy(), FakeActions()).reply(request("你好", history=history))
    kinds = [(type(m).__name__, m.content) for m in seen[0]]
    assert kinds == [("SystemMessage", SYSTEM), ("HumanMessage", "早"), ("AIMessage", "早安"),
                     ("HumanMessage", "你好")]


def should_raise_agent_unavailable_when_the_model_fails():
    class Failing(ScriptedChatModel):
        def _generate(self, *args, **kwargs):
            raise RuntimeError("model down")

    with pytest.raises(AgentUnavailableError):
        LangChainAgentRunner(Failing(), FakeActions()).reply(request())


def should_raise_agent_unavailable_when_the_model_never_stops_calling_tools():
    from langchain_core.outputs import ChatGeneration, ChatResult

    class Looping(ScriptedChatModel):
        def _generate(self, *args, **kwargs):
            call = {"name": "get_latest_vitals", "args": {}, "id": uuid.uuid4().hex,
                    "type": "tool_call"}
            message = AIMessage("", tool_calls=[call])
            return ChatResult(generations=[ChatGeneration(message=message)])

    with pytest.raises(AgentUnavailableError):
        LangChainAgentRunner(Looping(), FakeActions()).reply(request())


def should_raise_agent_unavailable_when_the_final_answer_is_empty():
    from langchain_core.outputs import ChatGeneration, ChatResult

    class Empty(ScriptedChatModel):
        def _generate(self, *args, **kwargs):
            return ChatResult(generations=[ChatGeneration(message=AIMessage(""))])

    with pytest.raises(AgentUnavailableError):
        LangChainAgentRunner(Empty(), FakeActions()).reply(request())
