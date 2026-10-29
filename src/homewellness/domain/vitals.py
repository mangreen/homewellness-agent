"""Health measurements from the device. All values are validated on creation."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from homewellness.domain.errors import InvalidVitalsError

# A reading older than this is not used for safety decisions.
DEFAULT_VITALS_MAX_AGE = timedelta(minutes=30)


@dataclass(frozen=True, slots=True)
class BloodPressure:
    systolic: int
    diastolic: int

    def __post_init__(self) -> None:
        if not 50 <= self.systolic <= 300:
            raise InvalidVitalsError(f"systolic out of range: {self.systolic}")
        if not 30 <= self.diastolic <= 200:
            raise InvalidVitalsError(f"diastolic out of range: {self.diastolic}")
        if self.systolic <= self.diastolic:
            raise InvalidVitalsError("systolic must be above diastolic")

    def __str__(self) -> str:
        return f"{self.systolic}/{self.diastolic}"


@dataclass(frozen=True, slots=True)
class VitalsSnapshot:
    elder_id: str
    measured_at: datetime
    blood_pressure: BloodPressure | None = None
    heart_rate_bpm: int | None = None
    room_temperature_c: float | None = None

    def __post_init__(self) -> None:
        if self.measured_at.tzinfo is None:
            raise InvalidVitalsError("measured_at must have a time zone")
        if (
            self.blood_pressure is None
            and self.heart_rate_bpm is None
            and self.room_temperature_c is None
        ):
            raise InvalidVitalsError("snapshot has no measurement")
        if self.heart_rate_bpm is not None and not 20 <= self.heart_rate_bpm <= 250:
            raise InvalidVitalsError(f"heart rate out of range: {self.heart_rate_bpm}")
        if self.room_temperature_c is not None and not -20.0 <= self.room_temperature_c <= 60.0:
            raise InvalidVitalsError(f"room temperature out of range: {self.room_temperature_c}")

    def is_fresh(self, now: datetime, max_age: timedelta = DEFAULT_VITALS_MAX_AGE) -> bool:
        return now - self.measured_at <= max_age


@dataclass(frozen=True, slots=True)
class SleepSummary:
    """Sleep of the last night. `woke_on` is the local date the elder woke up."""

    elder_id: str
    woke_on: date
    hours_asleep: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.hours_asleep <= 24.0:
            raise InvalidVitalsError(f"sleep hours out of range: {self.hours_asleep}")
