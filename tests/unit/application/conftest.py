from types import SimpleNamespace

import pytest

from builders import make_profile, taipei
from homewellness.infrastructure.in_memory import (
    FixedClock,
    InMemoryClaimStore,
    InMemoryConversationRepository,
    InMemoryElderRepository,
    InMemoryIntakeRepository,
    InMemoryTelemetryRepository,
    RecordingNotifier,
)


@pytest.fixture
def env():
    """All in-memory adapters. The clock starts at 08:05 Taipei time."""
    return SimpleNamespace(
        clock=FixedClock(taipei(8, 5)),
        elders=InMemoryElderRepository([make_profile()]),
        telemetry=InMemoryTelemetryRepository(),
        intakes=InMemoryIntakeRepository(),
        claims=InMemoryClaimStore(),
        notifier=RecordingNotifier(),
        conversations=InMemoryConversationRepository(),
    )
