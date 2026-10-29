"""Notifier stand-in. The demo UI reads the sent list."""

import threading

from homewellness.models.interaction import Notification


class RecordingNotifier:
    """Keeps sent notifications in a list. The demo UI reads this list."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.sent: list[Notification] = []
        self.fail_next = False  # Test hook: the next send raises once.

    def send(self, notification: Notification) -> None:
        with self._lock:
            if self.fail_next:
                self.fail_next = False
                raise RuntimeError("notifier unavailable")
            self.sent.append(notification)
