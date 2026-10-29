"""Alert rules. These rules run as code. The LLM cannot override them.

NOTE: All thresholds are demo values. A clinician must review them before real use.
"""

from dataclasses import dataclass
from enum import StrEnum

from homewellness.domain.symptoms import RED_FLAG_SYMPTOMS, Symptom
from homewellness.domain.vitals import BloodPressure


class AlertLevel(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationAction(StrEnum):
    NONE = "none"
    NOTIFY_FAMILY = "notify_family"
    CALL_EMERGENCY = "call_emergency"


@dataclass(frozen=True, slots=True)
class AlertThresholds:
    elevated_systolic: int = 135
    elevated_diastolic: int = 85
    high_systolic: int = 160
    high_diastolic: int = 100
    critical_systolic: int = 180
    critical_diastolic: int = 120
    low_systolic: int = 90
    low_diastolic: int = 60


DEFAULT_THRESHOLDS = AlertThresholds()


def assess_blood_pressure(
    bp: BloodPressure, thresholds: AlertThresholds = DEFAULT_THRESHOLDS
) -> AlertLevel:
    t = thresholds
    if bp.systolic >= t.critical_systolic or bp.diastolic >= t.critical_diastolic:
        return AlertLevel.CRITICAL
    if bp.systolic >= t.high_systolic or bp.diastolic >= t.high_diastolic:
        return AlertLevel.HIGH
    if bp.systolic >= t.elevated_systolic or bp.diastolic >= t.elevated_diastolic:
        return AlertLevel.ELEVATED
    if bp.systolic < t.low_systolic or bp.diastolic < t.low_diastolic:
        return AlertLevel.LOW
    return AlertLevel.NORMAL


@dataclass(frozen=True, slots=True)
class EscalationDecision:
    action: EscalationAction
    reason: str


_ABNORMAL_LEVELS = frozenset({AlertLevel.LOW, AlertLevel.HIGH, AlertLevel.CRITICAL})
_SYMPTOM_NOTIFY_LEVELS = frozenset({AlertLevel.LOW, AlertLevel.ELEVATED, AlertLevel.HIGH})


def decide_escalation(level: AlertLevel | None, symptoms: frozenset[Symptom]) -> EscalationDecision:
    """Return the action for a blood pressure level and the reported symptoms.

    `level` is None when no fresh blood pressure reading exists.
    """
    has_red_flag = bool(symptoms & RED_FLAG_SYMPTOMS)
    if has_red_flag and level in _ABNORMAL_LEVELS:
        return EscalationDecision(
            EscalationAction.CALL_EMERGENCY, "red_flag_symptom_with_abnormal_bp"
        )
    if level is AlertLevel.CRITICAL:
        return EscalationDecision(EscalationAction.NOTIFY_FAMILY, "critical_bp")
    if has_red_flag:
        return EscalationDecision(EscalationAction.NOTIFY_FAMILY, "red_flag_symptom")
    if symptoms and level in _SYMPTOM_NOTIFY_LEVELS:
        return EscalationDecision(EscalationAction.NOTIFY_FAMILY, "symptom_with_abnormal_bp")
    return EscalationDecision(EscalationAction.NONE, "no_action_needed")
