from datetime import date, timedelta

import pytest

from builders import make_schedule, make_sleep, make_vitals, taipei
from homewellness.models.alert_policy import AlertLevel
from homewellness.models.trigger_policy import TriggerKind, evaluate_triggers


def run(local_now, taken=frozenset(), vitals=None, sleep=None):
    return evaluate_triggers(
        local_now=local_now, schedule=make_schedule(), taken_dose_ids=taken,
        vitals=vitals, sleep=sleep,
    )


def kinds(triggers):
    return [t.kind for t in triggers]


def should_trigger_medication_reminder_when_dose_is_due_and_not_taken():
    triggers = run(taipei(8, 5))
    assert kinds(triggers) == [TriggerKind.MEDICATION_DUE]
    assert triggers[0].dose.dose_id == "am"
    assert triggers[0].dedup_key == "med:2026-10-27:am"


@pytest.mark.parametrize(("hour", "minute"), [(7, 59), (10, 0)])
def should_not_trigger_medication_reminder_when_dose_is_upcoming_or_missed(hour, minute):
    assert run(taipei(hour, minute)) == []


def should_not_trigger_medication_reminder_when_dose_is_taken():
    assert run(taipei(8, 5), taken=frozenset({"am"})) == []


@pytest.mark.parametrize(
    ("systolic", "diastolic", "level"),
    [(160, 80, AlertLevel.HIGH), (188, 121, AlertLevel.CRITICAL), (85, 60, AlertLevel.LOW)],
)
def should_trigger_abnormal_vitals_when_fresh_reading_is_low_high_or_critical(
    systolic, diastolic, level
):
    now = taipei(12, 0)
    triggers = run(now, vitals=make_vitals(now, systolic, diastolic))
    assert kinds(triggers) == [TriggerKind.ABNORMAL_VITALS]
    assert triggers[0].alert_level is level
    assert str(triggers[0].blood_pressure) == f"{systolic}/{diastolic}"


@pytest.mark.parametrize(("systolic", "diastolic"), [(120, 80), (158, 98)])
def should_not_trigger_abnormal_vitals_when_reading_is_normal_or_only_elevated(systolic, diastolic):
    now = taipei(12, 0)
    assert run(now, vitals=make_vitals(now, systolic, diastolic)) == []


def should_not_trigger_abnormal_vitals_when_reading_is_stale():
    now = taipei(12, 31)
    assert run(now, vitals=make_vitals(taipei(12, 0), 188, 121)) == []


def should_use_measurement_time_in_dedup_key_when_vitals_trigger():
    now = taipei(12, 0)
    first = run(now, vitals=make_vitals(now, 188, 121))
    later = run(now + timedelta(minutes=1), vitals=make_vitals(now, 188, 121))
    assert first[0].dedup_key == later[0].dedup_key


def should_trigger_poor_sleep_when_hours_are_below_threshold_on_the_wake_date():
    triggers = run(taipei(12, 0), sleep=make_sleep(4.5))
    assert kinds(triggers) == [TriggerKind.POOR_SLEEP]
    assert (triggers[0].sleep_hours, triggers[0].dedup_key) == (4.5, "sleep:2026-10-27")


def should_not_trigger_poor_sleep_when_hours_equal_the_threshold():
    assert run(taipei(12, 0), sleep=make_sleep(5.0)) == []


def should_not_trigger_poor_sleep_when_summary_is_from_a_previous_day():
    assert run(taipei(12, 0), sleep=make_sleep(4.0, woke_on=date(2026, 10, 26))) == []


def should_order_triggers_by_priority_when_several_apply():
    now = taipei(8, 5)
    triggers = run(now, vitals=make_vitals(now, 188, 121), sleep=make_sleep(4.5))
    assert kinds(triggers) == [
        TriggerKind.ABNORMAL_VITALS, TriggerKind.MEDICATION_DUE, TriggerKind.POOR_SLEEP,
    ]
