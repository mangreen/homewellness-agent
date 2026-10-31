"""The OpenAI-compatible protocol (OpenAI and OpenRouter) through the real LangChain client.

A fake HTTP server replaces the network. It plays a tool-calling model:
read the vitals, ask the policy, answer.
"""

import json

import httpx
import pytest

from builders import make_health_context
from homewellness.models.interaction import AgentRequest
from homewellness.services.agent import LangChainAgentRunner
from homewellness.services.llm_factory import build_chat_model
from homewellness.settings import Settings
from tests_support import FakeActions

SYSTEM = "稱呼：王奶奶\n家屬：小美\n現在時間：12:00\n"
ANSWER = "王奶奶，您的血壓是 158/98，有點偏高。我已經先通知小美了。請先坐下休息，好嗎？"


def completion(message, finish):
    return httpx.Response(200, json={
        "id": "cmpl-1", "object": "chat.completion", "created": 0, "model": "m",
        "choices": [{"index": 0, "message": message, "finish_reason": finish}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})


def tool_call(name, arguments):
    call = {"id": f"call_{name}", "type": "function",
            "function": {"name": name, "arguments": json.dumps(arguments)}}
    return completion({"role": "assistant", "content": None, "tool_calls": [call]}, "tool_calls")


@pytest.fixture
def server():
    seen = []

    def handler(request):
        body = json.loads(request.content)
        seen.append((request, body))
        tool_results = [m for m in body["messages"] if m["role"] == "tool"]
        if not tool_results:
            return tool_call("get_latest_vitals", {})
        if len(tool_results) == 1:
            return tool_call("escalate_emergency", {"symptoms": ["dizziness"]})
        return completion({"role": "assistant", "content": ANSWER}, "stop")

    return seen, httpx.Client(transport=httpx.MockTransport(handler))


@pytest.mark.parametrize(("provider", "url", "model"), [
    ("openrouter", "https://openrouter.ai/api/v1/chat/completions",
     "nvidia/nemotron-3-ultra-550b-a55b:free"),
    ("openai", "https://api.openai.com/v1/chat/completions", "gpt-5.4-mini")])
def should_run_the_tool_loop_when_the_server_speaks_the_openai_protocol(
    server, provider, url, model
):
    seen, client = server
    settings = Settings(store_backend="memory", llm_provider=provider,
                        **{f"{provider}_api_key": "test-key"})
    actions = FakeActions()
    request = AgentRequest("e1", "我今天頭有點暈", make_health_context("e1"), (), SYSTEM)

    runner = LangChainAgentRunner(build_chat_model(settings, http_client=client), actions)
    reply = runner.reply(request)

    assert reply == ANSWER
    assert actions.calls == [
        ("get_latest_vitals", "e1"), ("escalate_emergency", "e1", ["dizziness"])]
    first, body = seen[0]
    assert (str(first.url), first.headers["authorization"], body["model"]) == (
        url, "Bearer test-key", model)
    assert {t["function"]["name"] for t in body["tools"]} == {
        "get_latest_vitals", "get_medication_status", "log_medication_intake", "escalate_emergency"}
    assert body["messages"][0] == {"role": "system", "content": SYSTEM}
    assert body["messages"][-1] == {"role": "user", "content": "我今天頭有點暈"}
    assert "temperature" not in body


def should_send_a_title_header_to_openrouter(server):
    seen, client = server
    settings = Settings(store_backend="memory", llm_provider="openrouter", openrouter_api_key="k")
    request = AgentRequest("e1", "你好", make_health_context("e1"), (), SYSTEM)
    model = build_chat_model(settings, http_client=client)
    LangChainAgentRunner(model, FakeActions()).reply(request)
    assert seen[0][0].headers["x-title"] == "HomeWellness Companion PoC"


def should_give_the_provider_message_in_the_detail_when_the_provider_refuses():
    from homewellness.models.errors import AgentUnavailableError

    def handler(request):
        return httpx.Response(404, json={"error": {
            "message": "No endpoints found matching your data policy", "code": 404}})

    settings = Settings(store_backend="memory", llm_provider="openrouter", openrouter_api_key="k")
    client = httpx.Client(transport=httpx.MockTransport(handler))
    model = build_chat_model(settings, http_client=client)
    request = AgentRequest("e1", "你好", make_health_context("e1"), (), SYSTEM)
    with pytest.raises(AgentUnavailableError) as caught:
        LangChainAgentRunner(model, FakeActions()).reply(request)
    assert "NotFoundError (HTTP 404)" in caught.value.detail
    assert "data policy" in caught.value.detail and "settings/privacy" in caught.value.detail
    assert "data policy" not in str(caught.value)  # The public message stays short.
