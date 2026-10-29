"""Rehearsal: the whole demo story through the real page, the real API, MQTT and DynamoDB.

Run with the stack up: `make rehearse`. It is the same path that you click during the demo.
"""

import os
import time
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from api_client import build_client

pytestmark = pytest.mark.rehearsal
PAGE = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")


def chat_texts(at):
    return [m.markdown[0].value for m in at.chat_message if m.markdown]


# NOTE: Streamlit turns a leading emoji into the icon, so the text starts after it.
def urgent_alerts(at):
    return [e.value for e in at.error if "緊急通報" in e.value]


def notice_alerts(at):
    return [w.value for w in at.warning if "通知家人" in w.value]


def wait_until(at, condition, what, timeout=20.0):
    """Run the page again and again, like the 2-second refresh, until the condition holds."""
    deadline = time.monotonic() + timeout
    while True:
        at.run()
        if condition(at):
            return
        if time.monotonic() > deadline:
            raise AssertionError(f"timeout: {what}\nchat: {chat_texts(at)}")
        time.sleep(0.4)


def should_play_the_whole_story_in_the_browser_page():
    if not os.environ.get("API_URL"):
        pytest.skip("API_URL is not set")
    started = time.monotonic()
    at = AppTest.from_file(PAGE, default_timeout=30)
    at.session_state["client"] = build_client()
    at.run()
    assert not at.exception

    at.button(key="reset").click().run()  # Start from a clean state.
    wait_until(at, lambda a: chat_texts(a) == [], "empty conversation after reset")

    # Scene A: the device sends data, the agent speaks first.
    at.button(key="sc-morning").click().run()
    wait_until(at, lambda a: any("早安" in t for t in chat_texts(a)), "morning greeting")
    at.button(key="q-1").click().run()  # 吃了
    wait_until(at, lambda a: any("記下" in t for t in chat_texts(a)), "intake recorded")

    # Scene B: dizzy, the agent reads the vitals and informs the family.
    at.button(key="sc-dizzy").click().run()
    wait_until(at, lambda a: any(m.value == "158/98" for m in a.metric), "vitals 158/98")
    at.button(key="q-0").click().run()  # 我今天頭有點暈
    wait_until(at, lambda a: any("158/98" in t and "小美" in t for t in chat_texts(a)), "dizzy reply")
    assert len(notice_alerts(at)) == 1

    # Scene C: critical reading, chest tightness, emergency alert.
    at.button(key="sc-crisis").click().run()
    wait_until(at, lambda a: any("188/121" in t for t in chat_texts(a)), "critical greeting")
    at.button(key="q-2").click().run()  # 我胸口有點悶
    wait_until(at, lambda a: any("119" in t for t in chat_texts(a)), "emergency reply")
    assert len(urgent_alerts(at)) == 1

    # Scene D: a repeat sends no second alert. The agent remembers the medicine.
    at.button(key="q-2").click().run()
    at.run()
    assert len(urgent_alerts(at)) == 1 and len(notice_alerts(at)) == 1
    at.button(key="q-3").click().run()  # 我今天吃藥了嗎？
    wait_until(at, lambda a: any("已經吃過" in t for t in chat_texts(a)), "medicine memory")

    # The reset clears everything, so the story can start again.
    at.button(key="reset").click().run()
    wait_until(at, lambda a: chat_texts(a) == [] and not urgent_alerts(a), "clean after reset")
    print(f"\nrehearsal finished in {time.monotonic() - started:.1f}s")
