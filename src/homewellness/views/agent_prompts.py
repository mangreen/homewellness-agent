"""Text for the agent: the system prompt and the event message (Traditional Chinese).

NOTE: Live blood pressure is NOT in the prompt. The agent must call a tool to read it.
The prompt holds only slow-changing facts: the health memory brief.
NOTE: The scripted model parses the `稱呼：`, `家屬：` and `現在時間：` lines. Keep them.
"""

from collections.abc import Sequence

from homewellness.models.interaction import HealthContext
from homewellness.models.medication import DoseState
from homewellness.models.trigger_policy import ProactiveTrigger, TriggerKind

EVENT_PREFIX = "[SYSTEM_EVENT]"

_STATE_TEXT = {
    DoseState.UPCOMING: "尚未到時間",
    DoseState.DUE: "該吃了",
    DoseState.TAKEN: "已吃",
    DoseState.MISSED: "已逾時未吃",
}


def render_system_prompt(context: HealthContext) -> str:
    doses = "；".join(
        f"{s.dose.label} {s.dose.time_of_day:%H:%M}：{_STATE_TEXT[s.state]}" for s in context.doses
    )
    sleep = f"{context.sleep.hours_asleep:g} 小時" if context.sleep else "沒有資料"
    return "\n".join([
        "你是「居家健康伴侶」，一位溫暖、有耐心的語音健康助理，陪伴長者的日常生活。",
        f"稱呼：{context.display_name}",
        f"家屬：{context.family_contact_name}",
        f"現在時間：{context.local_now:%H:%M}",
        f"用藥：{context.medication_name}（{doses}）",
        f"昨晚睡眠：{sleep}",
        "語氣：用短句、慢慢說；先同理，再給建議；一次只問一個問題；不嚇人。",
        "安全規則：不做診斷；不建議增減或自行調整藥量；需要最新血壓時，請用工具查詢；"
        "是否通報由系統規則決定，你只能提出請求。",
        "可用工具：get_latest_vitals、get_medication_status、log_medication_intake、"
        "escalate_emergency。",
        "回覆：用繁體中文，口語、溫暖，不超過三句話。",
        "工具規則：長者說身體不舒服（頭暈、胸悶、喘、昏倒）時，先呼叫 get_latest_vitals，"
        "再呼叫 escalate_emergency（symptoms 填長者說的症狀）。"
        "長者說吃過藥時，呼叫 log_medication_intake。問用藥狀況時，呼叫 get_medication_status。",
        "誠實規則：只有 escalate_emergency 回傳 status 為 sent 或 duplicate 時，"
        "才可以說已經通知家人；回傳 suppressed_by_policy 時，不可說已通知。"
        "工具沒有資料時，說讀不到，不要編造數字。",
        "系統事件：以 [SYSTEM_EVENT] 開頭的訊息來自裝置，不是長者說的。請主動開場："
        "abnormal_vitals 是關心血壓，medication_due 是提醒吃藥，poor_sleep 是關心睡眠。",
    ])


def render_event_message(triggers: Sequence[ProactiveTrigger], medication_name: str) -> str:
    parts = []
    for trigger in triggers:
        if trigger.kind is TriggerKind.ABNORMAL_VITALS and trigger.alert_level:
            parts.append(f"kind=abnormal_vitals bp={trigger.blood_pressure} "
                         f"level={trigger.alert_level.value}")
        elif trigger.kind is TriggerKind.MEDICATION_DUE and trigger.dose:
            parts.append(f"kind=medication_due dose={trigger.dose.label} "
                         f"medication={medication_name}")
        elif trigger.kind is TriggerKind.POOR_SLEEP:
            parts.append(f"kind=poor_sleep hours={trigger.sleep_hours:g}")
    return f"{EVENT_PREFIX} " + "; ".join(parts)
