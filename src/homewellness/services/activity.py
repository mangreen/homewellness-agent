"""A short log of what happens behind the scenes. The demo UI shows it as a timeline."""

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime

from homewellness.interfaces import Clock


@dataclass(frozen=True, slots=True)
class ActivityEvent:
    at: datetime
    kind: str  # clock | device | trigger | tool | alert
    text: str


class ActivityLog:
    def __init__(self, clock: Clock, max_events: int = 200) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        self._events: deque[ActivityEvent] = deque(maxlen=max_events)

    def add(self, kind: str, text: str) -> None:
        event = ActivityEvent(self._clock.now(), kind, text)
        with self._lock:
            self._events.append(event)

    def recent(self, limit: int) -> list[ActivityEvent]:
        """Return the newest events, oldest first."""
        with self._lock:
            return list(self._events)[-limit:]

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
