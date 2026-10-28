"""A scripted stand-in for a real LLM. It stays offline and needs no key.

It is a real LangChain chat model. It runs the same tool-calling loop as a real model:
it asks for a tool, reads the tool result, then answers. A real model replaces it
in `bootstrap.py` without a change in any controller.

NOTE: It matches keywords. It cannot understand free speech. The demo uses fixed phrases.
"""

import json
import re
import uuid
from dataclasses import dataclass
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from homewellness.models.symptoms import Symptom

EVENT_PREFIX = "[SYSTEM_EVENT]"

_SYMPTOM_PATTERNS = (
    (Symptom.FAINTING, re.compile("昏倒|昏厥|暈倒|快暈過去|眼前一黑")),
    (Symptom.CHEST_PAIN, re.compile("胸口|胸悶|胸痛|心口")),
    (Symptom.SHORTNESS_OF_BREATH, re.compile("喘|呼吸困難|呼吸不順|透不過氣")),
    (Symptom.DIZZINESS, re.compile("頭暈|頭昏|暈")),
)
_DOSAGE = re.compile("多吃|少吃|加量|減量|雙倍|兩顆|二顆|多一顆|停藥|不吃藥|不想吃藥")
_INTAKE = re.compile("吃了|吃過|服用了|吃完")
_QUESTION = re.compile("嗎|？|\\?|有沒有|了沒")
_LEVEL_TEXT = {
    "low": "有點偏低", "normal": "在正常範圍", "elevated": "有點偏高", "high": "偏高",
    "critical": "很高",
}


@dataclass(frozen=True)
class _Persona:
    name: str
    family: str
    hour: int


class ScriptedChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ScriptedChatModel":
        return self  # The script already knows the tool names.

    def _generate(self, messages: list[BaseMessage], stop: list[str] | None = None,
                  run_manager: Any = None, **kwargs: Any) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=_respond(messages))])


def _text(message: BaseMessage) -> str:
    return message.content if isinstance(message.content, str) else ""


def _persona(messages: list[BaseMessage]) -> _Persona:
    prompt = next((_text(m) for m in messages if isinstance(m, SystemMessage)), "")

    def find(pattern: str, default: str) -> str:
        found = re.search(pattern, prompt)
        return found.group(1) if found else default

    return _Persona(find(r"稱呼：(\S+)", "您"), find(r"家屬：(\S+)", "家人"),
                    int(find(r"現在時間：(\d{1,2}):\d{2}", "12")))


def _turn(messages: list[BaseMessage]) -> tuple[str, dict[str, dict]]:
    """Return the last human text and the tool results of the current turn."""
    last = max(i for i, m in enumerate(messages) if isinstance(m, HumanMessage))
    names: dict[str, str] = {}
    results: dict[str, dict] = {}
    for message in messages[last + 1:]:
        if isinstance(message, AIMessage):
            names.update({call["id"]: call["name"] for call in message.tool_calls})
        elif isinstance(message, ToolMessage):
            try:
                results[names.get(message.tool_call_id, "?")] = json.loads(_text(message))
            except json.JSONDecodeError:
                results[names.get(message.tool_call_id, "?")] = {}
    return _text(messages[last]), results


def _call(name: str, args: dict) -> AIMessage:
    call = {"name": name, "args": args, "id": f"call_{uuid.uuid4().hex[:12]}", "type": "tool_call"}
    return AIMessage(content="", tool_calls=[call])


def _respond(messages: list[BaseMessage]) -> AIMessage:
    persona = _persona(messages)
    text, results = _turn(messages)
    if text.startswith(EVENT_PREFIX):
        return AIMessage(_greeting(text, persona))

    symptoms = sorted(s.value for s, pattern in _SYMPTOM_PATTERNS if pattern.search(text))
    if symptoms:
        if "get_latest_vitals" not in results:
            return _call("get_latest_vitals", {})
        if "escalate_emergency" not in results:
            return _call("escalate_emergency", {"symptoms": symptoms})
        return AIMessage(_symptom_reply(persona, results["get_latest_vitals"],
                                        results["escalate_emergency"]))
    if _DOSAGE.search(text):
        return AIMessage(
            f"{persona.name}，藥量的事要聽醫師或藥師的，我沒辦法幫您決定。"
            f"請您先照醫師交代的方式服藥，有疑問我可以請{persona.family}幫您問問藥師，好嗎？"
        )
    if "藥" in text and _QUESTION.search(text):
        if "get_medication_status" not in results:
            return _call("get_medication_status", {})
        return AIMessage(_status_reply(persona, results["get_medication_status"]))
    if _INTAKE.search(text):
        if "log_medication_intake" not in results:
            return _call("log_medication_intake", {})
        return AIMessage(_intake_reply(persona, results["log_medication_intake"]))
    return AIMessage(
        f"{persona.name}，我在這裡陪您。您可以跟我說今天哪裡不舒服，也可以問我吃藥的時間。"
    )


def _symptom_reply(p: _Persona, vitals: dict, escalation: dict) -> str:
    if vitals.get("available"):
        level = _LEVEL_TEXT.get(vitals.get("level", ""), "")
        seen = f"您的血壓是 {vitals['blood_pressure']}，{level}。"
    else:
        seen = "我暫時讀不到手環最新的血壓。"
    action = escalation.get("action")
    if action == "call_emergency":
        return (f"{p.name}，{seen}我已經通知{p.family}和緊急聯絡窗口了。"
                "請您先坐下或躺下，不要自己走動。如果更不舒服，請馬上撥打 119。")
    if action == "notify_family":
        return (f"{p.name}，{seen}我已經先通知{p.family}了。"
                "請您先坐下來休息，10 分鐘後再量一次，好嗎？")
    if vitals.get("available"):
        return f"{p.name}，{seen}可能是站起來太快或昨晚沒睡好。先坐下喝點溫水休息一下，好嗎？"
    return f"{p.name}，{seen}請您先坐下休息，如果更不舒服要馬上告訴我，好嗎？"


def _intake_reply(p: _Persona, result: dict) -> str:
    dose = result.get("dose")
    status = result.get("status")
    if status == "recorded":
        return f"好的，{p.name}，我幫您記下{dose}的藥吃過了。身體有不舒服，隨時告訴我。"
    if status == "already_taken":
        return f"{p.name}，{dose}的藥我這邊已經記錄吃過了，不用再吃喔。"
    return f"{p.name}，現在還不到吃藥的時間，我先不記錄。時間到了我會提醒您。"


def _status_reply(p: _Persona, status: dict) -> str:
    by_state: dict[str, list[dict]] = {}
    for dose in status.get("doses", []):
        by_state.setdefault(dose["state"], []).append(dose)
    if "due" in by_state:
        label = by_state["due"][0]["label"]
        return f"{p.name}，{label}的藥還沒吃，現在就是吃藥的時間了。吃好了跟我說一聲，好嗎？"
    if "missed" in by_state:
        label = by_state["missed"][0]["label"]
        return (f"{p.name}，{label}的藥我這邊還沒有記錄到。如果不確定有沒有吃，"
                f"請先不要多吃，我可以請{p.family}幫您確認，好嗎？")
    if "taken" in by_state:
        return f"{p.name}，{by_state['taken'][-1]['label']}的藥已經吃過了。"
    upcoming = by_state.get("upcoming", [{"label": "下一次", "time": ""}])[0]
    return f"{p.name}，今天還沒到吃藥的時間，下一次是{upcoming['label']} {upcoming['time']}。"


def _greeting(text: str, p: _Persona) -> str:
    parts = text[len(EVENT_PREFIX):].split(";")
    events = [dict(re.findall(r"(\w+)=(\S+)", part)) for part in parts]
    kinds = {event.get("kind"): event for event in events}
    hello = "早安" if 5 <= p.hour < 11 else "午安" if 11 <= p.hour < 18 else "晚安"

    if "abnormal_vitals" in kinds:
        bp, level = kinds["abnormal_vitals"]["bp"], kinds["abnormal_vitals"]["level"]
        if level == "critical":
            return (f"{p.name}，我看到您的血壓是 {bp}，數值很高。請您先坐下來，不要走動。"
                    "您現在有沒有胸口悶或喘不過氣？")
        if level == "high":
            return f"{p.name}，我看到您的血壓是 {bp}，有點高。您現在覺得怎麼樣？"
        return f"{p.name}，我看到您的血壓是 {bp}，有點低。您現在有沒有覺得頭暈？"

    parts = [f"{hello}，{p.name}！"]
    if "poor_sleep" in kinds:
        parts.append(f"昨晚您好像只睡了 {kinds['poor_sleep']['hours']} 小時，辛苦了。")
    if "medication_due" in kinds:
        due = kinds["medication_due"]
        parts.append(f"現在是{due['dose']}要吃{due['medication']}的時間，吃好了跟我說一聲，好嗎？")
    elif "poor_sleep" in kinds:
        parts.append("今天身體有哪裡不舒服嗎？")
    return "".join(parts)
