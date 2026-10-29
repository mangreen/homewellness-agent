from builders import ELDER_ID, make_profile, make_sleep, make_vitals, taipei
from homewellness.controllers.health_context import build_health_context
from homewellness.models.alert_policy import AlertLevel
from homewellness.models.medication import Dose
from homewellness.models.trigger_policy import ProactiveTrigger, TriggerKind
from homewellness.models.vitals import BloodPressure
from homewellness.views.agent_prompts import render_event_message, render_system_prompt


def context(env):
    return build_health_context(
        profile=make_profile(), telemetry=env.telemetry, intakes=env.intakes, now=env.clock.now()
    )


def should_describe_the_elder_the_family_the_time_and_the_doses_in_the_system_prompt(env):
    env.telemetry.save_sleep(make_sleep(4.5))
    prompt = render_system_prompt(context(env))
    for expected in ("稱呼：王奶奶", "家屬：小美", "現在時間：08:05", "blood pressure medicine",
                     "morning 08:00：該吃了", "evening 20:00：尚未到時間", "昨晚睡眠：4.5 小時"):
        assert expected in prompt


def should_keep_live_blood_pressure_out_of_the_system_prompt(env):
    env.telemetry.save_vitals(make_vitals(taipei(8, 0), 158, 98))
    assert "158/98" not in render_system_prompt(context(env))


def should_say_that_sleep_is_unknown_when_there_is_no_summary(env):
    assert "昨晚睡眠：沒有資料" in render_system_prompt(context(env))


def should_state_the_safety_rules_in_the_system_prompt(env):
    prompt = render_system_prompt(context(env))
    assert "不做診斷" in prompt and "藥量" in prompt and "一次只問一個問題" in prompt


def should_render_one_event_line_for_each_trigger_kind():
    triggers = [
        ProactiveTrigger(TriggerKind.ABNORMAL_VITALS, "v", alert_level=AlertLevel.CRITICAL,
                         blood_pressure=BloodPressure(188, 121)),
        ProactiveTrigger(TriggerKind.MEDICATION_DUE, "m",
                         dose=Dose("am", "早上", taipei(8).time())),
        ProactiveTrigger(TriggerKind.POOR_SLEEP, "s", sleep_hours=4.5),
    ]
    assert render_event_message(triggers, "降血壓藥") == (
        "[SYSTEM_EVENT] kind=abnormal_vitals bp=188/121 level=critical; "
        "kind=medication_due dose=早上 medication=降血壓藥; kind=poor_sleep hours=4.5"
    )


def should_not_use_the_elder_id_in_the_prompt(env):
    assert ELDER_ID not in render_system_prompt(context(env))


def should_skip_a_trigger_when_its_data_is_incomplete():
    incomplete = [ProactiveTrigger(TriggerKind.MEDICATION_DUE, "m"),
                  ProactiveTrigger(TriggerKind.POOR_SLEEP, "s", sleep_hours=5.0)]
    assert render_event_message(incomplete, "降血壓藥") == "[SYSTEM_EVENT] kind=poor_sleep hours=5"
