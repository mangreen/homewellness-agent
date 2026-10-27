"""In-memory stores. They serve unit tests and the offline fallback.

NOTE: Every store is thread-safe. Real stores must keep the same contracts.
"""

import threading
from collections import defaultdict
from datetime import date

from homewellness.models.elder import ElderProfile
from homewellness.models.errors import ElderNotFoundError
from homewellness.models.interaction import ConversationTurn
from homewellness.models.medication import MedicationIntake
from homewellness.models.vitals import SleepSummary, VitalsSnapshot


class InMemoryElderStore:
    def __init__(self, profiles: list[ElderProfile]) -> None:
        self._profiles = {p.elder_id: p for p in profiles}

    def get(self, elder_id: str) -> ElderProfile:
        try:
            return self._profiles[elder_id]
        except KeyError:
            raise ElderNotFoundError(f"elder not found: {elder_id}") from None


class InMemoryTelemetryStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._vitals: dict[str, VitalsSnapshot] = {}
        self._sleep: dict[str, SleepSummary] = {}

    def save_vitals(self, snapshot: VitalsSnapshot) -> None:
        with self._lock:
            current = self._vitals.get(snapshot.elder_id)
            # Keep the newest reading. Events can arrive out of order.
            if current is None or snapshot.measured_at >= current.measured_at:
                self._vitals[snapshot.elder_id] = snapshot

    def latest_vitals(self, elder_id: str) -> VitalsSnapshot | None:
        with self._lock:
            return self._vitals.get(elder_id)

    def save_sleep(self, summary: SleepSummary) -> None:
        with self._lock:
            current = self._sleep.get(summary.elder_id)
            if current is None or summary.woke_on >= current.woke_on:
                self._sleep[summary.elder_id] = summary

    def latest_sleep(self, elder_id: str) -> SleepSummary | None:
        with self._lock:
            return self._sleep.get(elder_id)


class InMemoryIntakeStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: dict[tuple[str, date, str], MedicationIntake] = {}

    def add(self, intake: MedicationIntake) -> bool:
        key = (intake.elder_id, intake.local_date, intake.dose_id)
        with self._lock:
            if key in self._items:
                return False
            self._items[key] = intake
            return True

    def list_for_date(self, elder_id: str, local_date: date) -> list[MedicationIntake]:
        with self._lock:
            return [i for (e, d, _), i in self._items.items() if e == elder_id and d == local_date]


class InMemoryClaimStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._keys: set[str] = set()

    def try_claim(self, key: str) -> bool:
        with self._lock:
            if key in self._keys:
                return False
            self._keys.add(key)
            return True

    def release(self, key: str) -> None:
        with self._lock:
            self._keys.discard(key)


class InMemoryConversationStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._turns: dict[str, list[ConversationTurn]] = defaultdict(list)

    def append(self, elder_id: str, turn: ConversationTurn) -> None:
        with self._lock:
            self._turns[elder_id].append(turn)

    def recent(self, elder_id: str, limit: int) -> list[ConversationTurn]:
        with self._lock:
            return list(self._turns[elder_id][-limit:])
