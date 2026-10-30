import view_models as vm


def should_show_the_taipei_time_when_the_api_sends_a_utc_time():
    assert vm.local_time("2026-10-28T00:05:30+00:00") == "08:05"
    assert vm.local_time("2026-10-28T00:05:30+00:00", with_seconds=True) == "08:05:30"


def should_name_each_blood_pressure_level():
    assert [vm.level_badge(x) for x in ("low", "normal", "elevated", "high", "critical", None)] == [
        "🔵 偏低", "🟢 正常", "🟡 偏高", "🟠 高", "🔴 危急", "—"]


def should_describe_each_dose_with_its_state():
    rows = vm.dose_rows([
        {"dose_id": "am", "label": "早上", "time": "08:00", "state": "taken"},
        {"dose_id": "pm", "label": "晚上", "time": "20:00", "state": "upcoming"},
    ])
    assert rows == ["早上 08:00　✅ 已吃", "晚上 20:00　⏳ 尚未到時間"]


def should_describe_alerts_in_plain_words():
    alert = {"action": "call_emergency", "recipients": ["family", "emergency_services"],
             "body": "請立即聯絡本人", "created_at": "2026-10-28T00:40:00+00:00", "title": "緊急通報"}
    row = vm.alert_row(alert)
    assert row["urgent"] is True
    assert row["text"] == "🚨 08:40　緊急通報 → 家人、緊急聯絡窗口\n請立即聯絡本人"


def should_mark_a_family_notice_as_not_urgent():
    alert = {"action": "notify_family", "recipients": ["family"], "body": "b",
             "created_at": "2026-10-28T00:20:00+00:00", "title": "健康提醒"}
    assert vm.alert_row(alert)["urgent"] is False and "通知家人" in vm.alert_row(alert)["text"]


def should_list_activity_newest_first_with_an_icon():
    events = [{"at": "2026-10-28T00:05:00+00:00", "kind": "clock", "text": "（Demo）時間設為 08:05"},
              {"at": "2026-10-28T00:05:01+00:00", "kind": "tool", "text": "Agent 呼叫工具：x"}]
    assert vm.activity_rows(events) == [
        "🔧 08:05:01　Agent 呼叫工具：x", "🕗 08:05:00　（Demo）時間設為 08:05"]


def should_offer_three_scenarios_and_four_quick_replies():
    assert [s[0] for s in vm.SCENARIOS] == ["morning", "dizzy", "crisis"]
    assert len(vm.QUICK_REPLIES) == 4


def should_label_the_offline_brain_without_a_warning():
    assert vm.brain_label({"provider": "fake", "model": "scripted", "external": False,
                           "fallback": False}) == "🧩 離線模型（不連外網）"


def should_label_a_real_brain_with_the_provider_and_the_model():
    brain = {"provider": "anthropic", "model": "claude-haiku-5-5", "external": True, "fallback": True}
    assert vm.brain_label(brain) == "☁️ Claude｜claude-haiku-5-5（失敗時改用離線模型）"
    brain.update(provider="openrouter", fallback=False)
    assert vm.brain_label(brain) == "☁️ OpenRouter｜claude-haiku-5-5"


def should_show_no_label_when_the_brain_is_unknown():
    assert vm.brain_label(None) == ""


def should_use_a_brain_icon_for_the_fallback_event():
    row = vm.activity_rows([{"at": "2026-10-28T00:05:00+00:00", "kind": "llm", "text": "改用離線模型"}])
    assert row == ["🧠 08:05:00　改用離線模型"]
