from concurrent.futures import ThreadPoolExecutor

import pytest

from builders import ELDER_ID, make_vitals, taipei
from homewellness.controllers.escalation import EscalationController, EscalationStatus
from homewellness.models.alert_policy import EscalationAction
from homewellness.models.interaction import Recipient
from homewellness.models.symptoms import Symptom


@pytest.fixture
def use_case(env):
    return EscalationController(
        elders=env.elders, telemetry=env.telemetry, claims=env.claims,
        notifier=env.notifier, clock=env.clock,
    )


def seed_bp(env, systolic, diastolic, at=None):
    env.clock.set(taipei(12, 5))
    env.telemetry.save_vitals(make_vitals(at or taipei(12, 0), systolic, diastolic))


def should_send_emergency_notification_when_bp_is_critical_and_chest_pain_is_reported(
    use_case, env
):
    seed_bp(env, 188, 121)
    outcome = use_case.escalate(ELDER_ID, frozenset({Symptom.CHEST_PAIN}), "key-1")
    sent = env.notifier.sent
    assert outcome.status is EscalationStatus.SENT
    assert len(sent) == 1
    assert sent[0].action is EscalationAction.CALL_EMERGENCY
    assert set(sent[0].recipients) == {Recipient.FAMILY, Recipient.EMERGENCY_SERVICES}
    assert "188/121" in sent[0].body and "119" in sent[0].body


def should_notify_family_only_when_bp_is_critical_without_symptoms(use_case, env):
    seed_bp(env, 188, 121)
    use_case.escalate(ELDER_ID, frozenset(), "key-1")
    assert env.notifier.sent[0].action is EscalationAction.NOTIFY_FAMILY
    assert env.notifier.sent[0].recipients == (Recipient.FAMILY,)


def should_notify_family_when_dizziness_comes_with_elevated_bp(use_case, env):
    seed_bp(env, 158, 98)
    use_case.escalate(ELDER_ID, frozenset({Symptom.DIZZINESS}), "key-1")
    assert "158/98" in env.notifier.sent[0].body
    assert "頭暈" in env.notifier.sent[0].body


def should_suppress_alert_when_policy_finds_no_reason_to_escalate(use_case, env):
    seed_bp(env, 120, 80)
    outcome = use_case.escalate(ELDER_ID, frozenset({Symptom.DIZZINESS}), "key-1")
    assert outcome.status is EscalationStatus.SUPPRESSED_BY_POLICY
    assert env.notifier.sent == []


def should_ignore_stale_reading_when_it_is_older_than_the_max_age(use_case, env):
    seed_bp(env, 188, 121)
    env.clock.set(taipei(13, 0))
    outcome = use_case.escalate(ELDER_ID, frozenset({Symptom.DIZZINESS}), "key-1")
    assert outcome.status is EscalationStatus.SUPPRESSED_BY_POLICY


def should_still_notify_family_when_a_red_flag_comes_without_a_fresh_reading(use_case, env):
    outcome = use_case.escalate(ELDER_ID, frozenset({Symptom.CHEST_PAIN}), "key-1")
    assert outcome.status is EscalationStatus.SENT
    assert env.notifier.sent[0].action is EscalationAction.NOTIFY_FAMILY


def should_return_duplicate_when_the_same_key_is_used_twice(use_case, env):
    seed_bp(env, 188, 121)
    use_case.escalate(ELDER_ID, frozenset({Symptom.CHEST_PAIN}), "key-1")
    second = use_case.escalate(ELDER_ID, frozenset({Symptom.CHEST_PAIN}), "key-1")
    assert second.status is EscalationStatus.DUPLICATE
    assert len(env.notifier.sent) == 1


def should_send_a_new_alert_when_the_key_is_different(use_case, env):
    seed_bp(env, 188, 121)
    use_case.escalate(ELDER_ID, frozenset({Symptom.CHEST_PAIN}), "key-1")
    use_case.escalate(ELDER_ID, frozenset({Symptom.CHEST_PAIN}), "key-2")
    assert len(env.notifier.sent) == 2


def should_release_the_key_and_allow_retry_when_the_notifier_fails(use_case, env):
    seed_bp(env, 188, 121)
    env.notifier.fail_next = True
    with pytest.raises(RuntimeError):
        use_case.escalate(ELDER_ID, frozenset({Symptom.CHEST_PAIN}), "key-1")
    retry = use_case.escalate(ELDER_ID, frozenset({Symptom.CHEST_PAIN}), "key-1")
    assert retry.status is EscalationStatus.SENT
    assert len(env.notifier.sent) == 1


@pytest.mark.concurrency
def should_send_one_alert_when_ten_requests_use_the_same_key_at_the_same_time(use_case, env):
    seed_bp(env, 188, 121)
    symptoms = frozenset({Symptom.CHEST_PAIN})
    with ThreadPoolExecutor(max_workers=10) as pool:
        statuses = list(
            pool.map(lambda _: use_case.escalate(ELDER_ID, symptoms, "same").status, range(10))
        )
    assert statuses.count(EscalationStatus.SENT) == 1
    assert statuses.count(EscalationStatus.DUPLICATE) == 9
    assert len(env.notifier.sent) == 1
