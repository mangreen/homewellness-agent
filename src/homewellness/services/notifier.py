"""Notifier stand-in. The demo UI reads the sent list."""

import threading
from collections.abc import Callable

from homewellness.models.interaction import Notification


class RecordingNotifier:
    def __init__(self, on_send: Callable[[Notification], None] | None = None) -> None:
        self._lock = threading.Lock()
        self._on_send = on_send
        self.sent: list[Notification] = []
        self.fail_next = False  # Test hook: the next send raises once.

    def list_sent(self) -> list[Notification]:
        with self._lock:
            return list(self.sent)

    def send(self, notification: Notification) -> None:
        with self._lock:
            if self.fail_next:
                self.fail_next = False
                raise RuntimeError("notifier unavailable")
            self.sent.append(notification)
        if self._on_send is not None:
            self._on_send(notification)

    def clear(self) -> None:
        with self._lock:
            self.sent.clear()
