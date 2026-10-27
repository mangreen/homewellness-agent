from datetime import UTC, time

import pytest

from builders import make_profile, make_schedule, taipei
from homewellness.models.errors import InvalidScheduleError
from homewellness.models.medication import (
    Dose,
    DoseState,
    IntakeStatus,
    MedicationSchedule,
    dose_states,
    resolve_intake,
)


def should_raise_invalid_schedule_when_there_are_no_doses():
    with pytest.raises(InvalidScheduleError):
        MedicationSchedule("medicine", ())


def should_raise_invalid_schedule_when_dose_ids_repeat():
    doses = (Dose("a", "one", time(8)), Dose("a", "two", time(9)))
    with pytest.raises(InvalidScheduleError):
        MedicationSchedule("medicine", doses)


def should_raise_invalid_profile_when_time_zone_is_unknown():
    profile = make_profile()
    with pytest.raises(InvalidScheduleError):
        type(profile)("e", "n", "f", "Mars/Olympus", profile.medication_schedule)


def should_convert_to_local_time_when_profile_receives_utc_time():
    utc_now = taipei(8, 5).astimezone(UTC)
    assert make_profile().local_now(utc_now).hour == 8


@pytest.mark.parametrize(
    ("hour", "minute", "expected"),
    [
        (7, 59, DoseState.UPCOMING),
        (8, 0, DoseState.DUE),
        (9, 59, DoseState.DUE),
        (10, 0, DoseState.MISSED),
    ],
)
def should_classify_dose_when_time_is_near_a_window_edge(hour, minute, expected):
    states = dose_states(make_schedule(), frozenset(), taipei(hour, minute))
    assert states["am"] is expected


def should_classify_dose_as_taken_when_it_is_in_the_taken_set():
    states = dose_states(make_schedule(), frozenset({"am"}), taipei(10, 30))
    assert states["am"] is DoseState.TAKEN


def should_record_dose_when_it_is_due_and_not_taken():
    result = resolve_intake(make_schedule(), frozenset(), taipei(8, 5))
    assert (result.status, result.dose.dose_id) == (IntakeStatus.RECORDED, "am")


def should_report_already_taken_when_the_dose_is_in_the_taken_set():
    result = resolve_intake(make_schedule(), frozenset({"am"}), taipei(8, 5))
    assert (result.status, result.dose.dose_id) == (IntakeStatus.ALREADY_TAKEN, "am")


def should_record_dose_when_time_is_exactly_at_the_early_window_start():
    result = resolve_intake(make_schedule(), frozenset(), taipei(7, 0))
    assert result.status is IntakeStatus.RECORDED


def should_report_no_dose_due_when_time_is_before_the_early_window():
    result = resolve_intake(make_schedule(), frozenset(), taipei(6, 59))
    assert (result.status, result.dose) == (IntakeStatus.NO_DOSE_DUE, None)


def should_record_late_dose_when_the_morning_dose_was_missed():
    result = resolve_intake(make_schedule(), frozenset(), taipei(11, 0))
    assert (result.status, result.dose.dose_id) == (IntakeStatus.RECORDED, "am")


def should_pick_the_most_recent_dose_when_two_doses_are_pending():
    result = resolve_intake(make_schedule(), frozenset(), taipei(20, 5))
    assert result.dose.dose_id == "pm"


def should_not_claim_an_older_dose_when_the_latest_dose_is_already_taken():
    result = resolve_intake(make_schedule(), frozenset({"pm"}), taipei(20, 5))
    assert (result.status, result.dose.dose_id) == (IntakeStatus.ALREADY_TAKEN, "pm")
