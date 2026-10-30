"""Text and format for the page. Pure functions, so they are easy to test."""

from datetime import datetime
from zoneinfo import ZoneInfo

TAIPEI = ZoneInfo("Asia/Taipei")

# NOTE: The scripted agent understands these fixed phrases. A test in the main repo checks it.
QUICK_REPLIES = ("我今天頭有點暈", "吃了", "我胸口有點悶", "我今天吃藥了嗎？")

SCENARIOS = (
    ("morning", "A", "早上主動關懷", "裝置回報睡眠 4.5 小時，Agent 先開口"),
    ("dizzy", "B", "血壓偏高", "裝置回報 158/98。接著說「我今天頭有點暈」"),
    ("crisis", "C", "血壓危急", "裝置回報 188/121。接著說「我胸口有點悶」"),
)

_LEVEL = {"low": "🔵 偏低", "normal": "🟢 正常", "elevated": "🟡 偏高", "high": "🟠 高",
          "critical": "🔴 危急"}
_DOSE_STATE = {"upcoming": "⏳ 尚未到時間", "due": "⏰ 該吃了", "taken": "✅ 已吃",
               "missed": "⚠️ 逾時未吃"}
_EVENT_ICON = {"clock": "🕗", "device": "📡", "trigger": "⚡", "tool": "🔧", "alert": "🚨",
               "llm": "🧠"}
_ACTION = {"notify_family": "通知家人", "call_emergency": "緊急通報"}
_RECIPIENT = {"family": "家人", "emergency_services": "緊急聯絡窗口"}


def local_time(iso: str, with_seconds: bool = False) -> str:
    moment = datetime.fromisoformat(iso).astimezone(TAIPEI)
    return moment.strftime("%H:%M:%S" if with_seconds else "%H:%M")


def level_badge(level: str | None) -> str:
    return _LEVEL.get(level or "", "—")


def dose_rows(doses: list[dict]) -> list[str]:
    return [f"{d['label']} {d['time']}　{_DOSE_STATE.get(d['state'], d['state'])}" for d in doses]


def alert_row(alert: dict) -> dict:
    recipients = "、".join(_RECIPIENT.get(r, r) for r in alert["recipients"])
    action = _ACTION.get(alert["action"], alert["action"])
    return {
        "urgent": alert["action"] == "call_emergency",
        "text": f"🚨 {local_time(alert['created_at'])}　{action} → {recipients}\n{alert['body']}",
    }


def activity_rows(events: list[dict]) -> list[str]:
    """Newest first. The API sends the oldest first."""
    return [
        f"{_EVENT_ICON.get(e['kind'], '•')} {local_time(e['at'], with_seconds=True)}　{e['text']}"
        for e in reversed(events)
    ]


_PROVIDER = {"anthropic": "Claude", "openai": "OpenAI", "openrouter": "OpenRouter"}


def brain_label(brain: dict | None) -> str:
    if not brain:
        return ""
    if not brain["external"]:
        return "🧩 離線模型（不連外網）"
    note = "（失敗時改用離線模型）" if brain["fallback"] else ""
    return f"☁️ {_PROVIDER.get(brain['provider'], brain['provider'])}｜{brain['model']}{note}"


def external_warning(brain: dict | None) -> str | None:
    if not brain or not brain["external"]:
        return None
    name = _PROVIDER.get(brain["provider"], brain["provider"])
    return (f"目前使用外部 LLM：對話內容與健康資料會送到 {name}。"
            "Demo 只用虛構資料，請勿輸入真實個資。")
