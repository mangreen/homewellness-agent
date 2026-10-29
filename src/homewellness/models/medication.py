"""Medication schedule and intake rules. Pure functions. No I/O."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum

from homewellness.models.errors import InvalidScheduleError

# A dose is DUE from its scheduled time until this window ends. Then it is MISSED.
DUE_WINDOW = timedelta(hours=2)
# An elder can record a dose this long before its scheduled time.
EARLY_WINDOW = timedelta(minutes=60)


@dataclass(frozen=True, slots=True)
class Dose:
    dose_id: str
    label: str
    time_of_day: time


@dataclass(frozen=True, slots=True)
class MedicationSchedule:
    medication_name: str
    doses: tuple[Dose, ...]

    def __post_init__(self) -> None:
        if not self.doses:
            raise InvalidScheduleError("schedule needs at least one dose")
        ids = [dose.dose_id for dose in self.doses]
        if len(set(ids)) != len(ids):
            raise InvalidScheduleError("dose ids must be unique")


@dataclass(frozen=True, slots=True)
class MedicationIntake:
    elder_id: str
    dose_id: str
    local_date: date
    taken_at: datetime


class DoseState(StrEnum):
    UPCOMING = "upcoming"
    DUE = "due"
    TAKEN = "taken"
    MISSED = "missed"


class IntakeStatus(StrEnum):
    RECORDED = "recorded"  # In `resolve_intake`: this dose is the one to record.
    ALREADY_TAKEN = "already_taken"
    NO_DOSE_DUE = "no_dose_due"


@dataclass(frozen=True, slots=True)
class IntakeResolution:
    status: IntakeStatus
    dose: Dose | None


def _scheduled_at(dose: Dose, local_now: datetime) -> datetime:
    return datetime.combine(local_now.date(), dose.time_of_day, tzinfo=local_now.tzinfo)


def dose_states(
    schedule: MedicationSchedule, taken_dose_ids: frozenset[str], local_now: datetime
) -> dict[str, DoseState]:
    states: dict[str, DoseState] = {}
    for dose in schedule.doses:
        scheduled = _scheduled_at(dose, local_now)
        if dose.dose_id in taken_dose_ids:
            states[dose.dose_id] = DoseState.TAKEN
        elif local_now < scheduled:
            states[dose.dose_id] = DoseState.UPCOMING
        elif local_now < scheduled + DUE_WINDOW:
            states[dose.dose_id] = DoseState.DUE
        else:
            states[dose.dose_id] = DoseState.MISSED
    return states


def resolve_intake(
    schedule: MedicationSchedule, taken_dose_ids: frozenset[str], local_now: datetime
) -> IntakeResolution:
    """Decide which dose "I took my medicine" refers to.

    NOTE: Only the most recent recordable dose is checked. An older missed dose is
    never recorded by accident. A false "taken" record is worse than a missed one.
    """
    recordable = [
        (_scheduled_at(dose, local_now), dose)
        for dose in schedule.doses
        if local_now >= _scheduled_at(dose, local_now) - EARLY_WINDOW
    ]
    if not recordable:
        return IntakeResolution(IntakeStatus.NO_DOSE_DUE, None)
    _, latest = max(recordable, key=lambda item: item[0])
    if latest.dose_id in taken_dose_ids:
        return IntakeResolution(IntakeStatus.ALREADY_TAKEN, latest)
    return IntakeResolution(IntakeStatus.RECORDED, latest)
