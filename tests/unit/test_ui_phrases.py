"""The UI offers fixed phrases. The scripted agent must understand every one of them."""

import importlib.util
from pathlib import Path

import pytest

from builders import make_health_context
from homewellness.models.interaction import AgentRequest
from homewellness.services.agent import LangChainAgentRunner
from homewellness.services.scripted_model import ScriptedChatModel
from tests_support import FakeActions

SYSTEM = "稱呼：王奶奶\n家屬：小美\n現在時間：08:05\n"
UI_VIEW_MODELS = Path(__file__).resolve().parents[2] / "ui" / "view_models.py"


def load_quick_replies():
    spec = importlib.util.spec_from_file_location("ui_view_models", UI_VIEW_MODELS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.QUICK_REPLIES


@pytest.mark.parametrize("phrase", load_quick_replies())
def should_make_the_agent_call_a_tool_when_a_quick_reply_is_sent(phrase):
    actions = FakeActions()
    request = AgentRequest("e1", phrase, make_health_context("e1"), (), SYSTEM)
    LangChainAgentRunner(ScriptedChatModel(), actions).reply(request)
    assert actions.calls, f"the agent did not call any tool for {phrase!r}"
