"""Notification text for family and emergency contacts (Traditional Chinese)."""

from datetime import datetime

from homewellness.models.alert_policy import EscalationAction, EscalationDecision
from homewellness.models.elder import ElderProfile
from homewellness.models.interaction import Notification, Recipient
from homewellness.models.symptoms import Symptom
from homewellness.models.vitals import BloodPressure

_SYMPTOM_TEXT = {
    Symptom.DIZZINESS: "頭暈",
    Symptom.CHEST_PAIN: "胸痛或胸悶",
    Symptom.SHORTNESS_OF_BREATH: "呼吸困難",
    Symptom.FAINTING: "昏厥",
}


def compose_notification(
    *,
    profile: ElderProfile,
    blood_pressure: BloodPressure | None,
    symptoms: frozenset[Symptom],
    decision: EscalationDecision,
    created_at: datetime,
) -> Notification:
    facts: list[str] = []
    if blood_pressure is not None:
        facts.append(f"目前血壓 {blood_pressure}")
    if symptoms:
        names = "、".join(_SYMPTOM_TEXT[s] for s in sorted(symptoms, key=lambda s: s.value))
        facts.append(f"回報{names}")
    summary = f"{profile.display_name}{'，'.join(facts)}。"

    if decision.action is EscalationAction.CALL_EMERGENCY:
        return Notification(
            profile.elder_id, decision.action, "緊急通報",
            f"{summary}請立即聯絡本人，必要時撥打 119。",
            (Recipient.FAMILY, Recipient.EMERGENCY_SERVICES), created_at,
        )
    return Notification(
        profile.elder_id, decision.action, "健康提醒",
        f"{summary}請盡快聯絡確認狀況。", (Recipient.FAMILY,), created_at,
    )
