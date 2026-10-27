from datetime import UTC, datetime, timedelta

from builders import taipei
from homewellness.services.clock import FixedClock, SimulatedClock


def should_follow_the_base_clock_when_no_time_was_set():
    base = FixedClock(datetime(2026, 1, 1, tzinfo=UTC))
    assert SimulatedClock(base).now() == base.now()


def should_jump_to_the_given_time_when_set_is_called():
    clock = SimulatedClock(FixedClock(datetime(2026, 1, 1, tzinfo=UTC)))
    clock.set(taipei(8, 5))
    assert clock.now() == taipei(8, 5)


def should_keep_moving_with_the_base_clock_after_a_jump():
    base = FixedClock(datetime(2026, 1, 1, tzinfo=UTC))
    clock = SimulatedClock(base)
    clock.set(taipei(8, 5))
    base.set(base.now() + timedelta(seconds=90))
    assert clock.now() == taipei(8, 5) + timedelta(seconds=90)
