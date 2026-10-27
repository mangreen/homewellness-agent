from concurrent.futures import ThreadPoolExecutor

import pytest

from builders import ELDER_ID, TODAY, make_sleep, make_vitals, taipei
from homewellness.application.evaluate_telemetry import EvaluateTelemetry
from homewellness.domain.errors import DomainError, ElderNotFoundError
from homewellness.domain.medication import MedicationIntake
from homewellness.domain.trigger_policy import TriggerKind


@pytest.fixture
def use_case(env):
    return EvaluateTelemetry(
        elders=env.elders, telemetry=env.telemetry, intakes=env.intakes,
        claims=env.claims, clock=env.clock,
    )


def should_return_medication_trigger_when_a_tick_runs_at_dose_time(use_case):
    triggers = use_case.execute(ELDER_ID)
    assert [t.kind for t in triggers] == [TriggerKind.MEDICATION_DUE]


def should_return_each_trigger_only_once_when_the_same_tick_runs_twice(use_case):
    first = use_case.execute(ELDER_ID)
    second = use_case.execute(ELDER_ID)
    assert (len(first), len(second)) == (1, 0)


def should_skip_medication_trigger_when_the_dose_is_already_taken(use_case, env):
    env.intakes.add(MedicationIntake(ELDER_ID, "am", TODAY, taipei(8, 2)))
    assert use_case.execute(ELDER_ID) == []


def should_save_reading_and_trigger_when_a_critical_reading_arrives(use_case, env):
    env.clock.set(taipei(12, 0))
    reading = make_vitals(taipei(12, 0), 188, 121)
    triggers = use_case.execute(ELDER_ID, reading)
    assert [t.kind for t in triggers] == [TriggerKind.ABNORMAL_VITALS]
    assert env.telemetry.latest_vitals(ELDER_ID) == reading


def should_save_sleep_and_trigger_when_poor_sleep_arrives(use_case, env):
    env.clock.set(taipei(12, 0))
    triggers = use_case.execute(ELDER_ID, make_sleep(4.5))
    assert [t.kind for t in triggers] == [TriggerKind.POOR_SLEEP]
    assert env.telemetry.latest_sleep(ELDER_ID).hours_asleep == 4.5


def should_raise_domain_error_when_the_reading_belongs_to_another_elder(use_case):
    with pytest.raises(DomainError):
        use_case.execute(ELDER_ID, make_sleep(4.5, elder_id="someone-else"))


def should_raise_not_found_when_the_elder_is_unknown(use_case):
    with pytest.raises(ElderNotFoundError):
        use_case.execute("unknown")


@pytest.mark.concurrency
def should_emit_each_trigger_once_when_ten_ticks_run_at_the_same_time(use_case):
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda _: use_case.execute(ELDER_ID), range(10)))
    assert sum(len(r) for r in results) == 1
