from types import SimpleNamespace

import pytest

from builders import make_profile, taipei
from homewellness.services.clock import FixedClock
from homewellness.services.notifier import RecordingNotifier
from homewellness.stores.memory import (
    InMemoryClaimStore,
    InMemoryConversationStore,
    InMemoryElderStore,
    InMemoryIntakeStore,
    InMemoryTelemetryStore,
)


@pytest.fixture
def env():
    """All in-memory adapters. The clock starts at 08:05 Taipei time."""
    return SimpleNamespace(
        clock=FixedClock(taipei(8, 5)),
        elders=InMemoryElderStore([make_profile()]),
        telemetry=InMemoryTelemetryStore(),
        intakes=InMemoryIntakeStore(),
        claims=InMemoryClaimStore(),
        notifier=RecordingNotifier(),
        conversations=InMemoryConversationStore(),
    )
