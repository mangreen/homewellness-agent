"""Clocks."""

import threading
from datetime import UTC, datetime, timedelta

from homewellness.interfaces import Clock


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def set(self, now: datetime) -> None:
        self._now = now


class SimulatedClock:
    """Follows a base clock with an offset. `set` changes the offset, then time keeps moving."""

    def __init__(self, base: Clock) -> None:
        self._base = base
        self._offset = timedelta(0)
        self._lock = threading.Lock()

    def now(self) -> datetime:
        with self._lock:
            return self._base.now() + self._offset

    def set(self, target: datetime) -> None:
        with self._lock:
            self._offset = target - self._base.now()
