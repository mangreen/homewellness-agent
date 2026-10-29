import httpx
import pytest

from api_client import ApiClient, ApiError, ApiUnavailable


def client_for(handler):
    return ApiClient(httpx.Client(base_url="http://api", transport=httpx.MockTransport(handler)))


def should_send_a_message_with_a_fresh_idempotency_key_each_time():
    seen = []

    def handler(request):
        seen.append((request.url.path, request.headers["Idempotency-Key"], request.content))
        return httpx.Response(200, json={"reply": "好的", "trace_id": "t"})

    api = client_for(handler)
    assert api.send_message("吃了") == "好的"
    api.send_message("吃了")
    assert seen[0][0] == "/elders/demo-elder-001/messages"
    assert seen[0][1] != seen[1][1] and len(seen[0][1]) >= 8
    assert "吃了" in seen[0][2].decode()


def should_return_the_turns_when_the_conversation_is_requested():
    api = client_for(lambda r: httpx.Response(200, json={"turns": [{"role": "agent", "text": "x"}]}))
    assert api.conversation(5) == [{"role": "agent", "text": "x"}]


def should_start_a_scenario_and_reset_with_idempotency_keys():
    paths = []

    def handler(request):
        paths.append((request.method, request.url.path, "Idempotency-Key" in request.headers))
        return httpx.Response(200, json={"status": "reset", "scenario": "morning", "published": 3})

    api = client_for(handler)
    assert api.start_scenario("morning")["status"] == "reset"  # The mock sends one body.
    assert api.reset()["status"] == "reset"
    assert paths == [("POST", "/sim/scenarios/morning", True), ("POST", "/demo/reset", True)]


def should_raise_api_error_with_the_code_and_trace_id_when_the_api_answers_with_an_error():
    body = {"error": {"code": "duplicate_request", "message": "m", "trace_id": "abc"}}
    api = client_for(lambda r: httpx.Response(409, json=body))
    with pytest.raises(ApiError) as caught:
        api.send_message("x")
    assert (caught.value.status, caught.value.code, caught.value.trace_id) == (
        409, "duplicate_request", "abc")


def should_raise_api_error_with_safe_defaults_when_the_error_body_is_not_json():
    api = client_for(lambda r: httpx.Response(502, text="bad gateway"))
    with pytest.raises(ApiError) as caught:
        api.status()
    assert (caught.value.status, caught.value.code) == (502, "http_error")


def should_raise_unavailable_when_the_api_cannot_be_reached():
    def handler(request):
        raise httpx.ConnectError("down")

    with pytest.raises(ApiUnavailable):
        client_for(handler).status()


def should_return_no_events_when_the_api_is_not_in_demo_mode():
    body = {"error": {"code": "not_found", "message": "m", "trace_id": "t"}}
    assert client_for(lambda r: httpx.Response(404, json=body)).activity() == []


def should_report_health_as_a_boolean():
    assert client_for(lambda r: httpx.Response(200, json={"status": "ok"})).health() is True
    assert client_for(lambda r: httpx.Response(503, json={"status": "starting"})).health() is False
