import io
import json
import logging
from typing import get_args

from fastapi.testclient import TestClient

from homewellness.api.app import create_app
from homewellness.api.schemas import ScenarioName
from homewellness.models.errors import AgentUnavailableError
from homewellness.observability import JsonFormatter
from homewellness.simulator.scenarios import SCENARIO_NAMES
from tests_support import ELDER, StubSubscriber, key

MESSAGES = f"/elders/{ELDER}/messages"


def send(client, text="你好", headers=None, path=MESSAGES):
    return client.post(path, json={"text": text},
                       headers={"Idempotency-Key": key()} if headers is None else headers)


# --- health and documentation ---------------------------------------------------------------

def should_answer_200_when_the_app_is_ready(client):
    assert client.get("/healthz").json() == {"status": "ok"}


def should_answer_503_when_the_mqtt_subscriber_is_not_ready(container):
    app = create_app(container, subscriber=StubSubscriber(False))
    assert TestClient(app).get("/healthz").status_code == 503


def should_keep_the_scenario_names_in_sync_with_the_simulator():
    assert get_args(ScenarioName) == SCENARIO_NAMES


def should_publish_an_openapi_document(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {MESSAGES.replace(ELDER, "{elder_id}"), "/alerts", "/healthz"} <= paths.keys()


# --- messages ---------------------------------------------------------------------------------

def should_return_the_reply_and_a_matching_trace_id_when_the_elder_sends_a_message(client):
    response = send(client)
    assert response.status_code == 200
    assert "王奶奶" in response.json()["reply"]
    assert response.json()["trace_id"] == response.headers["X-Trace-Id"] != "-"


def should_list_both_turns_when_the_conversation_is_requested(client):
    send(client, "你好")
    turns = client.get(f"/elders/{ELDER}/conversation").json()["turns"]
    assert [t["role"] for t in turns] == ["elder", "agent"]
    assert turns[0]["text"] == "你好" and "T" in turns[0]["at"]


def should_answer_400_when_the_idempotency_key_is_missing(client):
    response = send(client, headers={})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_idempotency_key"
    assert response.json()["error"]["trace_id"] == response.headers["X-Trace-Id"]


def should_answer_400_when_the_idempotency_key_has_a_bad_format(client):
    assert send(client, headers={"Idempotency-Key": "short"}).status_code == 400
    assert send(client, headers={"Idempotency-Key": "bad key with spaces!"}).status_code == 400


def should_answer_409_when_the_same_key_is_used_twice(client):
    headers = {"Idempotency-Key": key()}
    assert send(client, headers=headers).status_code == 200
    second = send(client, headers=headers)
    assert (second.status_code, second.json()["error"]["code"]) == (409, "duplicate_request")
    assert len(client.get(f"/elders/{ELDER}/conversation").json()["turns"]) == 2


def should_allow_a_retry_with_the_same_key_when_the_first_attempt_failed(client, container):
    class FlakyChat:
        calls = 0

        def reply(self, elder_id, text):
            FlakyChat.calls += 1
            if FlakyChat.calls == 1:
                raise AgentUnavailableError("down")
            return "ok"

    container.chat = FlakyChat()
    headers = {"Idempotency-Key": key()}
    first = send(client, headers=headers)
    assert (first.status_code, first.json()["error"]["code"]) == (503, "agent_unavailable")
    assert send(client, headers=headers).status_code == 200


def should_answer_422_without_echoing_the_input_when_the_body_is_not_valid(client):
    secret = "x" * 501
    for body in ({"text": secret}, {"text": ""}, {"text": "hi", "extra": 1}, {}):
        response = client.post(MESSAGES, json=body, headers={"Idempotency-Key": key()})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"
        assert "xxxxx" not in response.text and "input" not in response.json()["error"]


def should_answer_404_when_the_elder_does_not_exist(client):
    response = send(client, path="/elders/nobody/messages")
    assert (response.status_code, response.json()["error"]["code"]) == (404, "elder_not_found")


def should_answer_422_when_the_elder_id_has_forbidden_characters(client):
    assert send(client, path="/elders/bad!id/messages").status_code == 422


def should_answer_a_sanitized_404_when_the_route_does_not_exist(client):
    response = client.get("/nothing-here")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found" and response.json()["error"]["trace_id"]


def should_answer_a_sanitized_500_and_log_no_detail_when_something_breaks(client, container):
    class Exploding:
        def reply(self, elder_id, text):
            raise RuntimeError("secret-token-123")

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("homewellness.api")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    container.chat = Exploding()
    try:
        response = send(client)
    finally:
        logger.removeHandler(handler)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "secret-token-123" not in response.text and "Traceback" not in response.text
    assert "secret-token-123" not in stream.getvalue()
    assert '"error_type": "RuntimeError"' in stream.getvalue()


def should_log_each_request_with_the_trace_id_of_the_response(client):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("homewellness.api")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        response = client.get(f"/elders/{ELDER}/status")
    finally:
        logger.removeHandler(handler)
    entry = json.loads(stream.getvalue().splitlines()[-1])
    assert entry["event"] == "request" and entry["status"] == 200
    assert entry["trace_id"] == response.headers["X-Trace-Id"] and entry["user_id"] == ELDER


# --- status and alerts ------------------------------------------------------------------------

def should_describe_the_elder_when_the_status_is_requested(client):
    status = client.get(f"/elders/{ELDER}/status").json()
    assert (status["display_name"], status["local_time"], status["blood_pressure"]) == (
        "王奶奶", "15:00", None)
    assert [d["dose_id"] for d in status["doses"]] == ["am", "pm"]


def should_show_the_fresh_blood_pressure_when_a_reading_arrived(client):
    client.post("/sim/scenarios/dizzy", headers={"Idempotency-Key": key()})
    status = client.get(f"/elders/{ELDER}/status").json()
    assert (status["blood_pressure"], status["alert_level"]) == ("158/98", "elevated")


def should_list_no_alerts_when_nothing_was_sent(client):
    assert client.get("/alerts").json() == {"alerts": []}


# --- simulator --------------------------------------------------------------------------------

def should_publish_the_scenario_messages_when_a_scenario_is_started(client, publisher):
    response = client.post("/sim/scenarios/morning", headers={"Idempotency-Key": key()})
    assert response.json() == {"scenario": "morning", "published": 3}
    assert len(publisher.sent) == 3


def should_answer_404_when_demo_mode_is_off(container, publisher):
    container.settings = type(container.settings)(store_backend="memory", demo_mode=False)
    client = TestClient(create_app(container, publisher=publisher))
    response = client.post("/sim/scenarios/morning", headers={"Idempotency-Key": key()})
    assert response.status_code == 404


def should_answer_404_when_no_publisher_is_available(container):
    client = TestClient(create_app(container, publisher=None))
    response = client.post("/sim/scenarios/morning", headers={"Idempotency-Key": key()})
    assert response.status_code == 404


def should_answer_422_when_the_scenario_is_unknown(client):
    assert client.post("/sim/scenarios/nope", headers={"Idempotency-Key": key()}).status_code == 422


def should_answer_400_when_a_scenario_is_started_without_a_key(client):
    assert client.post("/sim/scenarios/morning").status_code == 400


def should_answer_422_when_a_domain_rule_is_broken_without_a_special_code(client, container):
    from homewellness.models.errors import DomainError

    class Strict:
        def reply(self, elder_id, text):
            raise DomainError("detail that must not leak")

    container.chat = Strict()
    response = send(client)
    assert (response.status_code, response.json()["error"]["code"]) == (422, "invalid_request")
    assert "must not leak" not in response.text


def should_start_and_stop_the_subscriber_and_close_the_publisher_with_the_app(container):
    events = []

    class Subscriber:
        def start(self):
            events.append("start")

        def stop(self):
            events.append("stop")

        def is_ready(self):
            return True

    class Publisher:
        def close(self):
            events.append("close")

    with TestClient(create_app(container, subscriber=Subscriber(), publisher=Publisher())) as c:
        assert c.get("/healthz").status_code == 200
    assert events == ["start", "stop", "close"]


def should_run_without_a_subscriber_and_a_publisher_when_none_are_given(container):
    with TestClient(create_app(container)) as c:
        assert c.get("/healthz").json() == {"status": "ok"}


# --- demo activity and reset -------------------------------------------------------------------

def should_list_the_activity_events_when_a_scenario_has_run(client):
    client.post("/sim/scenarios/morning", headers={"Idempotency-Key": key()})
    events = client.get("/demo/activity?limit=50").json()["events"]
    assert {e["kind"] for e in events} >= {"clock", "device", "trigger"}
    assert all({"at", "kind", "text"} <= e.keys() for e in events)


def should_answer_422_when_the_activity_limit_is_out_of_range(client):
    assert client.get("/demo/activity?limit=0").status_code == 422
    assert client.get("/demo/activity?limit=101").status_code == 422


def should_answer_404_for_activity_and_reset_when_demo_mode_is_off(container, publisher):
    container.settings = type(container.settings)(store_backend="memory", demo_mode=False)
    client = TestClient(create_app(container, publisher=publisher))
    assert client.get("/demo/activity").status_code == 404
    assert client.post("/demo/reset", headers={"Idempotency-Key": key()}).status_code == 404


def should_forget_the_story_when_the_demo_is_reset(client):
    client.post("/sim/scenarios/morning", headers={"Idempotency-Key": key()})
    send(client, "吃了")
    response = client.post("/demo/reset", headers={"Idempotency-Key": key()})
    assert response.json() == {"status": "reset"}
    assert client.get(f"/elders/{ELDER}/conversation").json()["turns"] == []
    assert client.get("/alerts").json() == {"alerts": []}
    assert client.get("/demo/activity").json() == {"events": []}


def should_answer_400_when_the_reset_has_no_idempotency_key(client):
    assert client.post("/demo/reset").status_code == 400


def should_describe_the_brain_when_the_demo_brain_is_requested(client):
    assert client.get("/demo/brain").json() == {
        "provider": "fake", "model": "scripted", "external": False, "fallback": False}


def should_tell_that_the_brain_is_external_when_a_real_provider_is_set(publisher):
    from homewellness.bootstrap import build_container
    from homewellness.settings import Settings

    settings = Settings(store_backend="memory", demo_mode=True, llm_provider="openrouter",
                        openrouter_api_key="k")
    app = create_app(build_container(settings), publisher=publisher)
    brain = TestClient(app).get("/demo/brain").json()
    assert (brain["provider"], brain["external"], brain["fallback"]) == ("openrouter", True, True)
    assert "key" not in str(brain).lower()


def should_answer_404_for_the_brain_when_demo_mode_is_off(container, publisher):
    container.settings = type(container.settings)(store_backend="memory", demo_mode=False)
    client = TestClient(create_app(container, publisher=publisher))
    assert client.get("/demo/brain").status_code == 404
