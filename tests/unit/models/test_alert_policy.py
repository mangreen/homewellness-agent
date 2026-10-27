import pytest

from homewellness.models.alert_policy import (
    AlertLevel,
    AlertThresholds,
    EscalationAction,
    assess_blood_pressure,
    decide_escalation,
)
from homewellness.models.symptoms import Symptom
from homewellness.models.vitals import BloodPressure

L, N, E, H, C = (AlertLevel.LOW, AlertLevel.NORMAL, AlertLevel.ELEVATED, AlertLevel.HIGH,
                 AlertLevel.CRITICAL)


@pytest.mark.parametrize(
    ("systolic", "diastolic", "expected"),
    [
        (120, 80, N), (134, 84, N), (90, 60, N),
        (135, 70, E), (120, 85, E), (158, 98, E), (159, 99, E),
        (160, 80, H), (130, 100, H), (179, 119, H),
        (180, 80, C), (130, 120, C), (188, 121, C),
        (89, 70, L), (110, 59, L),
    ],
)
def should_assess_level_when_bp_is_near_a_threshold(systolic, diastolic, expected):
    assert assess_blood_pressure(BloodPressure(systolic, diastolic)) is expected


def should_use_custom_thresholds_when_they_are_given():
    thresholds = AlertThresholds(elevated_systolic=120)
    assert assess_blood_pressure(BloodPressure(120, 70), thresholds) is E


S = Symptom


@pytest.mark.parametrize(
    ("level", "symptoms", "expected"),
    [
        (C, {S.CHEST_PAIN}, EscalationAction.CALL_EMERGENCY),
        (H, {S.SHORTNESS_OF_BREATH}, EscalationAction.CALL_EMERGENCY),
        (L, {S.FAINTING}, EscalationAction.CALL_EMERGENCY),
        (E, {S.CHEST_PAIN}, EscalationAction.NOTIFY_FAMILY),
        (N, {S.CHEST_PAIN}, EscalationAction.NOTIFY_FAMILY),
        (None, {S.CHEST_PAIN}, EscalationAction.NOTIFY_FAMILY),
        (C, set(), EscalationAction.NOTIFY_FAMILY),
        (C, {S.DIZZINESS}, EscalationAction.NOTIFY_FAMILY),
        (E, {S.DIZZINESS}, EscalationAction.NOTIFY_FAMILY),
        (H, {S.DIZZINESS}, EscalationAction.NOTIFY_FAMILY),
        (L, {S.DIZZINESS}, EscalationAction.NOTIFY_FAMILY),
        (N, {S.DIZZINESS}, EscalationAction.NONE),
        (None, {S.DIZZINESS}, EscalationAction.NONE),
        (H, set(), EscalationAction.NONE),
        (E, set(), EscalationAction.NONE),
        (L, set(), EscalationAction.NONE),
        (N, set(), EscalationAction.NONE),
        (None, set(), EscalationAction.NONE),
    ],
)
def should_decide_action_when_level_and_symptoms_are_given(level, symptoms, expected):
    assert decide_escalation(level, frozenset(symptoms)).action is expected


def should_explain_decision_with_reason_code_when_action_is_emergency():
    decision = decide_escalation(C, frozenset({S.CHEST_PAIN}))
    assert decision.reason == "red_flag_symptom_with_abnormal_bp"


def should_explain_decision_with_reason_code_when_no_action_is_needed():
    assert decide_escalation(N, frozenset()).reason == "no_action_needed"
