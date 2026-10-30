"""Headless tests of the page. The API is a stub, so no server is needed."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from api_client import ApiError, ApiUnavailable

PAGE = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")
STATUS = {"display_name": "王奶奶", "local_time": "08:05", "blood_pressure": "158/98",
          "alert_level": "elevated", "heart_rate_bpm": 80, "sleep_hours": 4.5,
          "doses": [{"dose_id": "am", "label": "早上", "time": "08:00", "state": "due"}]}
TURNS = [{"role": "agent", "text": "早安，王奶奶！", "at": "2026-10-28T00:05:00+00:00"},
         {"role": "elder", "text": "吃了", "at": "2026-10-28T00:06:00+00:00"}]
ALERT = {"action": "notify_family", "recipients": ["family"], "body": "請盡快聯絡",
         "created_at": "2026-10-28T00:20:00+00:00", "title": "健康提醒"}
EVENT = {"at": "2026-10-28T00:05:00+00:00", "kind": "tool", "text": "Agent 呼叫工具：get_latest_vitals"}


class StubClient:
    def __init__(self, turns=(), alerts=(), events=(), brain=None):
        self.calls = []
        self._brain = brain
        self.turns, self._alerts, self.events = list(turns), list(alerts), list(events)

    def health(self):
        return True

    def brain(self):
        return self._brain

    def conversation(self, limit=30):
        return self.turns

    def status(self):
        return STATUS

    def alerts(self):
        return self._alerts

    def activity(self, limit=30):
        return self.events

    def send_message(self, text):
        self.calls.append(("send", text))
        return "ok"

    def start_scenario(self, name):
        self.calls.append(("scenario", name))
        return {"scenario": name}

    def reset(self):
        self.calls.append(("reset",))
        return {"status": "reset"}


def open_page(client):
    at = AppTest.from_file(PAGE, default_timeout=20)
    at.session_state["client"] = client
    return at.run()


def texts(at):
    return [m.markdown[0].value for m in at.chat_message if m.markdown]


def should_show_the_conversation_with_two_speakers():
    at = open_page(StubClient(turns=TURNS))
    assert not at.exception
    assert [m.avatar for m in at.chat_message] == ["🤖", "👵"]
    assert texts(at) == ["早安，王奶奶！", "吃了"]


def should_show_a_hint_when_there_is_no_conversation_yet():
    at = open_page(StubClient())
    assert any("場景 A" in i.value for i in at.info)


def should_show_the_live_status_alerts_and_activity():
    at = open_page(StubClient(alerts=[ALERT], events=[EVENT]))
    metrics = {m.label: m.value for m in at.metric}
    assert metrics == {"Demo 時間": "08:05", "血壓": "158/98"}
    body = " ".join(m.value for m in at.markdown)
    assert "🟡 偏高" in body and "早上 08:00　⏰ 該吃了" in body
    assert "get_latest_vitals" in body
    assert any("通知家人" in w.value for w in at.warning)


def should_send_the_quick_reply_when_a_quick_reply_button_is_clicked():
    client = StubClient()
    at = open_page(client)
    at.button(key="q-2").click().run()
    assert client.calls == [("send", "我胸口有點悶")]


def should_send_the_typed_text_when_the_elder_types_a_message():
    client = StubClient()
    at = open_page(client)
    at.chat_input[0].set_value("你好").run()
    assert client.calls == [("send", "你好")]


@pytest.mark.parametrize(("key", "name"), [("sc-morning", "morning"), ("sc-dizzy", "dizzy"),
                                           ("sc-crisis", "crisis")])
def should_start_the_scenario_when_its_button_is_clicked(key, name):
    client = StubClient()
    open_page(client).button(key=key).click().run()
    assert client.calls == [("scenario", name)]


def should_reset_the_demo_when_the_reset_button_is_clicked():
    client = StubClient()
    at = open_page(client)
    at.button(key="reset").click().run()
    assert client.calls == [("reset",)] and any("已重置" in s.value for s in at.success)


def should_show_the_code_and_trace_id_when_the_api_answers_with_an_error():
    class Failing(StubClient):
        def send_message(self, text):
            raise ApiError(409, "duplicate_request", "This request was already handled.", "abc123")

    at = open_page(Failing())
    at.button(key="q-1").click().run()
    assert any("duplicate_request" in e.value and "abc123" in e.value for e in at.error)


def should_explain_what_to_do_when_the_api_is_unreachable():
    class Down(StubClient):
        def conversation(self, limit=30):
            raise ApiUnavailable("down")

        def status(self):
            raise ApiUnavailable("down")

    at = open_page(Down())
    assert not at.exception and any("make up" in e.value for e in at.error)


def should_show_the_offline_brain_without_a_warning():
    at = open_page(StubClient(brain={"provider": "fake", "model": "scripted", "external": False,
                                     "fallback": False}))
    assert any("離線模型" in c.value for c in at.caption)
    assert not any("資料會送到" in w.value for w in at.warning)


def should_warn_that_data_leaves_the_machine_when_the_brain_is_external():
    at = open_page(StubClient(brain={"provider": "openrouter", "model": "m:free", "external": True,
                                     "fallback": True}))
    assert any("OpenRouter" in c.value for c in at.caption)
    assert any("資料會送到 OpenRouter" in w.value for w in at.warning)


@pytest.mark.parametrize("index", [0, 1, 2, 3])
def should_keep_the_text_box_after_a_quick_reply_is_clicked(index):
    """Regression: `chosen or st.chat_input(...)` skipped the box when a button was clicked."""
    at = open_page(StubClient())
    assert len(at.chat_input) == 1
    at.button(key=f"q-{index}").click().run()
    assert len(at.chat_input) == 1


@pytest.mark.parametrize("key", ["sc-morning", "sc-dizzy", "sc-crisis", "reset"])
def should_keep_the_text_box_after_a_scenario_or_reset_is_clicked(key):
    at = open_page(StubClient())
    at.button(key=key).click().run()
    assert len(at.chat_input) == 1


def should_keep_the_text_box_after_many_clicks_in_a_row():
    at = open_page(StubClient())
    for key in ("q-0", "q-1", "q-2", "q-0", "sc-dizzy", "q-3", "q-1"):
        at.button(key=key).click().run()
        assert len(at.chat_input) == 1, f"the text box is missing after {key}"


def should_keep_the_text_box_after_a_typed_message():
    at = open_page(StubClient())
    at.chat_input[0].set_value("你好").run()
    assert len(at.chat_input) == 1
