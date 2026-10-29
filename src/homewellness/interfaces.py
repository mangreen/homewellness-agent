"""Interfaces for what we may swap: stores, clock, notifier and agent."""

from datetime import date, datetime
from typing import Protocol

from homewellness.models.elder import ElderProfile
from homewellness.models.interaction import AgentRequest, ConversationTurn, Notification
from homewellness.models.medication import MedicationIntake
from homewellness.models.vitals import SleepSummary, VitalsSnapshot


class Clock(Protocol):
    def now(self) -> datetime:
        """Return the current time. The value must have a time zone."""


class SettableClock(Clock, Protocol):
    """A clock that the demo can move."""

    def set(self, now: datetime) -> None: ...


class ElderStore(Protocol):
    def get(self, elder_id: str) -> ElderProfile:
        """Return the profile. Raise ElderNotFoundError if it does not exist."""


class TelemetryStore(Protocol):
    def save_vitals(self, snapshot: VitalsSnapshot) -> None: ...
    def latest_vitals(self, elder_id: str) -> VitalsSnapshot | None: ...
    def save_sleep(self, summary: SleepSummary) -> None: ...
    def latest_sleep(self, elder_id: str) -> SleepSummary | None: ...


class IntakeStore(Protocol):
    def add(self, intake: MedicationIntake) -> bool:
        """Store the intake. Return False if the same dose is already stored for that date.

        The check and the write must be one atomic step.
        """

    def list_for_date(self, elder_id: str, local_date: date) -> list[MedicationIntake]: ...


class ClaimStore(Protocol):
    """Atomic "first caller wins" store. It gives idempotency and de-duplication."""

    def try_claim(self, key: str) -> bool:
        """Return True for the first caller only."""

    def release(self, key: str) -> None:
        """Free a key so that a retry can claim it again."""


class Notifier(Protocol):
    def send(self, notification: Notification) -> None: ...


class ConversationStore(Protocol):
    def append(self, elder_id: str, turn: ConversationTurn) -> None: ...
    def recent(self, elder_id: str, limit: int) -> list[ConversationTurn]:
        """Return the latest turns, oldest first."""


class AgentRunner(Protocol):
    def reply(self, request: AgentRequest) -> str: ...
