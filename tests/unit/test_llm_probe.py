import json
from dataclasses import replace

import httpx

from homewellness.llm_eval import main, probe
from homewellness.settings import Settings

ROUTER = Settings(store_backend="memory", llm_provider="openrouter", openrouter_api_key="k")


def completion(message, finish="stop"):
    return httpx.Response(200, json={
        "id": "c", "object": "chat.completion", "created": 0, "model": "m",
        "choices": [{"index": 0, "message": message, "finish_reason": finish}]})


def client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def run(settings, handler):
    lines = []
    code = probe(settings, lines.append, http_client=client(handler))
    return code, "\n".join(lines)


def working(request):
    if json.loads(request.content).get("tools"):
        call = {"id": "c1", "type": "function", "function": {"name": "ping", "arguments": "{}"}}
        message = {"role": "assistant", "content": None, "tool_calls": [call]}
        return completion(message, "tool_calls")
    return completion({"role": "assistant", "content": "OK"})


def should_pass_both_steps_when_the_provider_answers_and_calls_the_tool():
    code, out = run(ROUTER, working)
    assert code == 0 and out.count("✅") == 2 and "ping" in out


def should_fail_the_second_step_when_the_model_ignores_the_tool():
    code, out = run(ROUTER, lambda r: completion({"role": "assistant", "content": "pong"}))
    assert code == 1 and "✅ 1/2" in out and "❌ 2/2" in out and "without calling the tool" in out


def should_stop_at_the_first_step_and_explain_when_the_provider_refuses():
    def refuse(request):
        body = {"error": {"message": "No endpoints found matching your data policy"}}
        return httpx.Response(404, json=body)

    code, out = run(ROUTER, refuse)
    assert code == 1 and "❌ 1/2" in out and "settings/privacy" in out and "2/2" not in out


def should_say_that_the_tool_is_unsupported_when_only_the_tool_step_fails():
    def only_plain(request):
        if json.loads(request.content).get("tools"):
            body = {"error": {"message": "No endpoints found that support tool use"}}
            return httpx.Response(404, json=body)
        return completion({"role": "assistant", "content": "OK"})

    code, out = run(ROUTER, only_plain)
    assert code == 1 and "✅ 1/2" in out and "❌ 2/2" in out and "cannot call tools" in out


def should_name_the_missing_key_variable():
    lines = []
    assert probe(replace(ROUTER, openrouter_api_key=None), lines.append) == 1
    assert "OPENROUTER_API_KEY" in lines[0]


def should_not_call_the_network_for_the_offline_model():
    lines = []
    assert probe(Settings(store_backend="memory"), lines.append) == 0
    assert "offline" in lines[0].lower()


def should_run_the_probe_from_the_command_line(capsys):
    assert main(["--probe"]) == 0
    assert "offline" in capsys.readouterr().out.lower()


def should_show_the_time_of_each_probe_step():
    import re

    _, out = run(ROUTER, working)
    assert len(re.findall(r"\(\d+\.\ds\)", out)) == 2
