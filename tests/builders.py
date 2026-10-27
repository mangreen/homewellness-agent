"""Test data builders. Keep tests short and focused on one behavior."""

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from homewellness.models.elder import ElderProfile
from homewellness.models.medication import Dose, MedicationSchedule
from homewellness.models.vitals import BloodPressure, SleepSummary, VitalsSnapshot

TAIPEI = ZoneInfo("Asia/Taipei")
ELDER_ID = "elder-001"
TODAY = date(2026, 10, 27)


def taipei(hour: int, minute: int = 0, day: date = TODAY) -> datetime:
    """Return an aware datetime in the Taipei time zone."""
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=TAIPEI)


def make_schedule() -> MedicationSchedule:
    return MedicationSchedule(
        medication_name="blood pressure medicine",
        doses=(Dose("am", "morning", time(8, 0)), Dose("pm", "evening", time(20, 0))),
    )


def make_profile(elder_id: str = ELDER_ID) -> ElderProfile:
    return ElderProfile(
        elder_id=elder_id,
        display_name="王奶奶",
        family_contact_name="小美",
        timezone="Asia/Taipei",
        medication_schedule=make_schedule(),
    )


def make_vitals(local_time: datetime, systolic: int = 120, diastolic: int = 80,
                elder_id: str = ELDER_ID) -> VitalsSnapshot:
    return VitalsSnapshot(
        elder_id, local_time.astimezone(UTC), blood_pressure=BloodPressure(systolic, diastolic)
    )


def make_sleep(hours: float, woke_on: date = TODAY, elder_id: str = ELDER_ID) -> SleepSummary:
    return SleepSummary(elder_id, woke_on, hours)
