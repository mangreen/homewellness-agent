import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from homewellness.services.scripted_model import ScriptedChatModel

MORNING_EVENT = (
    "[SYSTEM_EVENT] kind=medication_due dose=早上 medication=降血壓藥; kind=poor_sleep hours=4.5"
)
SYSTEM = "你是居家健康伴侶。\n稱呼：王奶奶\n家屬：小美\n現在時間：08:05\n"
NO_VITALS = {"available": False, "reason": "no_recent_reading"}


def vitals(bp="158/98", level="elevated"):
    return {"available": True, "blood_pressure": bp, "level": level, "heart_rate_bpm": 80,
            "measured_minutes_ago": 1}


def escalation(status="sent", action="notify_family"):
    return {"status": status, "action": action, "reason": "x"}


def ask(text, *steps, system=SYSTEM):
    """Build one turn. Each step is (tool name, tool args, tool result)."""
    messages = [SystemMessage(system), HumanMessage(text)]
    for index, (name, args, result) in enumerate(steps):
        call_id = f"call-{index}"
        messages.append(AIMessage("", tool_calls=[
            {"name": name, "args": args, "id": call_id, "type": "tool_call"}]))
        messages.append(ToolMessage(json.dumps(result, ensure_ascii=False), tool_call_id=call_id))
    return ScriptedChatModel().invoke(messages)


def names(reply):
    return [call["name"] for call in reply.tool_calls]


def should_read_vitals_first_when_the_elder_reports_dizziness():
    assert names(ask("我今天頭有點暈")) == ["get_latest_vitals"]


def should_ask_the_safety_policy_after_the_vitals_were_read():
    reply = ask("我今天頭有點暈", ("get_latest_vitals", {}, vitals()))
    assert names(reply) == ["escalate_emergency"]
    assert reply.tool_calls[0]["args"] == {"symptoms": ["dizziness"]}


def should_pass_red_flags_to_the_safety_policy_when_the_elder_reports_chest_tightness():
    reply = ask("我胸口有點悶", ("get_latest_vitals", {}, vitals("188/121", "critical")))
    assert reply.tool_calls[0]["args"] == {"symptoms": ["chest_pain"]}


def should_pass_every_symptom_in_sorted_order_when_several_are_reported():
    reply = ask("我頭暈又喘", ("get_latest_vitals", {}, vitals()))
    assert reply.tool_calls[0]["args"] == {"symptoms": ["dizziness", "shortness_of_breath"]}


def should_tell_the_family_was_notified_and_ask_for_a_rest_when_the_action_is_notify_family():
    reply = ask("我今天頭有點暈", ("get_latest_vitals", {}, vitals()),
                ("escalate_emergency", {"symptoms": ["dizziness"]}, escalation()))
    assert not reply.tool_calls
    for expected in ("158/98", "小美", "休息", "偏高"):
        assert expected in reply.content


@pytest.mark.parametrize("status", ["sent", "duplicate"])
def should_mention_119_when_the_action_is_call_emergency(status):
    reply = ask("我胸口悶", ("get_latest_vitals", {}, vitals("188/121", "critical")),
                ("escalate_emergency", {"symptoms": ["chest_pain"]},
                 escalation(status, "call_emergency")))
    assert "119" in reply.content and "小美" in reply.content and "188/121" in reply.content


def should_reassure_without_claiming_an_alert_when_the_policy_suppressed_it():
    reply = ask("我頭暈", ("get_latest_vitals", {}, vitals("120/80", "normal")),
                ("escalate_emergency", {"symptoms": ["dizziness"]},
                 escalation("suppressed_by_policy", "none")))
    assert "正常範圍" in reply.content and "通知" not in reply.content


def should_say_that_vitals_are_unavailable_when_the_wristband_has_no_recent_reading():
    reply = ask("我頭暈", ("get_latest_vitals", {}, NO_VITALS),
                ("escalate_emergency", {"symptoms": ["dizziness"]},
                 escalation("suppressed_by_policy", "none")))
    assert "讀不到" in reply.content


def should_record_the_dose_when_the_elder_says_the_medicine_was_taken():
    assert names(ask("吃了")) == ["log_medication_intake"]


@pytest.mark.parametrize(
    ("status", "expected"),
    [("recorded", "記下"), ("already_taken", "不用再吃"), ("no_dose_due", "還不到")],
)
def should_answer_by_intake_status_when_the_dose_was_resolved(status, expected):
    result = {"status": status, "dose": "早上"}
    assert expected in ask("我吃了藥", ("log_medication_intake", {}, result)).content


def should_read_the_medication_status_when_the_elder_asks_about_the_medicine():
    assert names(ask("我今天吃藥了嗎？")) == ["get_medication_status"]


@pytest.mark.parametrize(
    ("states", "expected"),
    [(("taken", "upcoming"), "已經吃過"), (("due", "upcoming"), "還沒吃"),
     (("missed", "upcoming"), "不要多吃"), (("upcoming", "upcoming"), "還沒到")],
)
def should_summarize_the_doses_when_the_status_is_known(states, expected):
    doses = [{"dose_id": "am", "label": "早上", "time": "08:00", "state": states[0]},
             {"dose_id": "pm", "label": "晚上", "time": "20:00", "state": states[1]}]
    result = {"medication": "降血壓藥", "doses": doses}
    assert expected in ask("吃藥了嗎？", ("get_medication_status", {}, result)).content


def should_refuse_to_change_the_dose_and_point_to_the_doctor():
    reply = ask("我可不可以多吃一顆藥")
    assert not reply.tool_calls and ("醫師" in reply.content or "藥師" in reply.content)


def should_stay_kind_and_use_the_name_when_the_message_is_not_understood():
    reply = ask("今天天氣真好")
    assert not reply.tool_calls and "王奶奶" in reply.content


def should_greet_about_sleep_and_medicine_when_the_morning_event_arrives():
    reply = ask(MORNING_EVENT)
    assert not reply.tool_calls
    for expected in ("早安", "王奶奶", "4.5", "早上", "降血壓藥"):
        assert expected in reply.content


def should_say_good_evening_when_the_clock_in_the_prompt_is_in_the_evening():
    event = "[SYSTEM_EVENT] kind=medication_due dose=晚上 medication=降血壓藥"
    assert "晚安" in ask(event, system=SYSTEM.replace("08:05", "20:05")).content


def should_ask_about_chest_symptoms_when_the_event_is_a_critical_reading():
    reply = ask("[SYSTEM_EVENT] kind=abnormal_vitals bp=188/121 level=critical")
    assert "188/121" in reply.content and "胸" in reply.content


def finals():
    full = ("get_latest_vitals", {}, vitals())
    esc = ("escalate_emergency", {"symptoms": ["dizziness"]}, escalation())
    return [
        ask("頭暈", full, esc),
        ask("我胸口悶", ("get_latest_vitals", {}, vitals("188/121", "critical")),
            ("escalate_emergency", {"symptoms": ["chest_pain"]},
             escalation("sent", "call_emergency"))),
        ask("吃了", ("log_medication_intake", {}, {"status": "recorded", "dose": "早上"})),
        ask("我可以多吃藥嗎"), ask("你好"),
        ask(MORNING_EVENT),
        ask("[SYSTEM_EVENT] kind=abnormal_vitals bp=188/121 level=critical"),
        ask("[SYSTEM_EVENT] kind=poor_sleep hours=4.5"),
    ]


@pytest.mark.parametrize("reply", finals())
def should_ask_at_most_one_question_in_every_reply(reply):
    assert reply.content.count("？") + reply.content.count("?") <= 1


@pytest.mark.parametrize("reply", finals())
def should_never_name_a_disease_or_make_a_diagnosis(reply):
    assert not any(word in reply.content for word in ("中風", "心肌梗", "心臟病", "診斷"))
