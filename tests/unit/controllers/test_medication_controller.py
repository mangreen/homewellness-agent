from concurrent.futures import ThreadPoolExecutor

import pytest

from builders import ELDER_ID, TODAY, taipei
from homewellness.controllers.medication import MedicationController
from homewellness.models.errors import ElderNotFoundError
from homewellness.models.medication import IntakeStatus


@pytest.fixture
def use_case(env):
    return MedicationController(elders=env.elders, intakes=env.intakes, clock=env.clock)


def should_record_intake_when_a_dose_is_due(use_case, env):
    result = use_case.record_intake(ELDER_ID)
    stored = env.intakes.list_for_date(ELDER_ID, TODAY)
    assert result.status is IntakeStatus.RECORDED
    assert [(i.dose_id, i.local_date) for i in stored] == [("am", TODAY)]


def should_report_already_taken_when_the_elder_confirms_twice(use_case, env):
    use_case.record_intake(ELDER_ID)
    second = use_case.record_intake(ELDER_ID)
    assert second.status is IntakeStatus.ALREADY_TAKEN
    assert len(env.intakes.list_for_date(ELDER_ID, TODAY)) == 1


def should_report_no_dose_due_when_it_is_too_early(use_case, env):
    env.clock.set(taipei(6, 0))
    assert use_case.record_intake(ELDER_ID).status is IntakeStatus.NO_DOSE_DUE
    assert env.intakes.list_for_date(ELDER_ID, TODAY) == []


def should_raise_not_found_when_the_elder_is_unknown(use_case):
    with pytest.raises(ElderNotFoundError):
        use_case.record_intake("unknown")


@pytest.mark.concurrency
def should_record_one_intake_when_ten_confirmations_arrive_at_the_same_time(use_case, env):
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda _: use_case.record_intake(ELDER_ID).status, range(10)))
    assert results.count(IntakeStatus.RECORDED) == 1
    assert results.count(IntakeStatus.ALREADY_TAKEN) == 9
    assert len(env.intakes.list_for_date(ELDER_ID, TODAY)) == 1


def should_report_already_taken_when_another_request_wins_the_race(env):
    class RacingIntakes:
        """The read shows no intake. The write finds that another request won."""

        def list_for_date(self, elder_id, local_date):
            return []

        def add(self, intake):
            return False

    use_case = MedicationController(elders=env.elders, intakes=RacingIntakes(), clock=env.clock)
    assert use_case.record_intake(ELDER_ID).status is IntakeStatus.ALREADY_TAKEN


def should_list_every_dose_with_its_state_when_the_status_is_requested(use_case):
    from homewellness.models.medication import DoseState

    assert [(d.dose.dose_id, d.state) for d in use_case.status(ELDER_ID)] == [
        ("am", DoseState.DUE), ("pm", DoseState.UPCOMING)]
