"""Elder profile. It owns the medication schedule."""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from homewellness.models.errors import InvalidScheduleError
from homewellness.models.medication import MedicationSchedule


@dataclass(frozen=True, slots=True)
class ElderProfile:
    elder_id: str
    display_name: str
    family_contact_name: str
    timezone: str  # IANA name, for example "Asia/Taipei"
    medication_schedule: MedicationSchedule

    def __post_init__(self) -> None:
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise InvalidScheduleError(f"unknown time zone: {self.timezone}") from error

    def local_now(self, now: datetime) -> datetime:
        return now.astimezone(ZoneInfo(self.timezone))
