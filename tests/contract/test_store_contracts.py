"""One contract for every store. In-memory and DynamoDB must behave the same."""

import uuid
from datetime import date, timedelta

import pytest

from builders import TODAY, make_sleep, make_vitals, taipei
from homewellness.models.interaction import ConversationTurn, Role
from homewellness.models.medication import MedicationIntake
from homewellness.models.vitals import BloodPressure, VitalsSnapshot
from homewellness.stores.memory import (
    InMemoryClaimStore,
    InMemoryConversationStore,
    InMemoryIntakeStore,
    InMemoryTelemetryStore,
)


@pytest.fixture(params=["memory", pytest.param("dynamodb", marks=pytest.mark.integration)])
def adapters(request):
    if request.param == "memory":
        return {
            "telemetry": InMemoryTelemetryStore(), "intakes": InMemoryIntakeStore(),
            "claims": InMemoryClaimStore(), "conversations": InMemoryConversationStore(),
        }
    from homewellness.stores.dynamodb import stores as r

    table = request.getfixturevalue("dynamo_table")
    return {
        "telemetry": r.DynamoTelemetryStore(table), "intakes": r.DynamoIntakeStore(table),
        "claims": r.DynamoClaimStore(table), "conversations": r.DynamoConversationStore(table),
    }


# --- TelemetryStore ---------------------------------------------------------------------

def should_return_none_when_no_vitals_exist(adapters, elder_id):
    assert adapters["telemetry"].latest_vitals(elder_id) is None


def should_return_the_newest_vitals_when_readings_arrive_out_of_order(adapters, elder_id):
    repo = adapters["telemetry"]
    repo.save_vitals(make_vitals(taipei(9, 0), 130, 80, elder_id))
    repo.save_vitals(make_vitals(taipei(8, 0), 188, 121, elder_id))
    assert str(repo.latest_vitals(elder_id).blood_pressure) == "130/80"


def should_keep_every_vitals_field_when_a_reading_is_stored(adapters, elder_id):
    original = VitalsSnapshot(elder_id, taipei(8, 0), BloodPressure(158, 98), 80, 24.5)
    adapters["telemetry"].save_vitals(original)
    assert adapters["telemetry"].latest_vitals(elder_id) == original


def should_keep_vitals_separate_when_two_elders_have_readings(adapters, elder_id):
    other = elder_id + "-other"
    adapters["telemetry"].save_vitals(make_vitals(taipei(8, 0), 120, 80, elder_id))
    assert adapters["telemetry"].latest_vitals(other) is None


def should_return_the_newest_sleep_when_summaries_arrive_out_of_order(adapters, elder_id):
    repo = adapters["telemetry"]
    repo.save_sleep(make_sleep(7.0, TODAY, elder_id))
    repo.save_sleep(make_sleep(4.0, TODAY - timedelta(days=1), elder_id))
    assert repo.latest_sleep(elder_id).hours_asleep == 7.0


# --- IntakeStore ------------------------------------------------------------------------

def intake(elder_id, dose_id="am", day=TODAY):
    return MedicationIntake(elder_id, dose_id, day, taipei(8, 5, day))


def should_accept_the_first_intake_and_reject_a_repeat_for_the_same_dose(adapters, elder_id):
    repo = adapters["intakes"]
    assert (repo.add(intake(elder_id)), repo.add(intake(elder_id))) == (True, False)


def should_list_only_the_intakes_of_the_given_elder_and_date(adapters, elder_id):
    repo = adapters["intakes"]
    repo.add(intake(elder_id, "am"))
    repo.add(intake(elder_id, "pm"))
    repo.add(intake(elder_id, "am", date(2026, 10, 26)))
    repo.add(intake(elder_id + "-other", "am"))
    assert sorted(i.dose_id for i in repo.list_for_date(elder_id, TODAY)) == ["am", "pm"]


# --- ClaimStore ------------------------------------------------------------------------------

def should_grant_a_claim_to_the_first_caller_only(adapters):
    key = f"k-{uuid.uuid4().hex}"
    assert (adapters["claims"].try_claim(key), adapters["claims"].try_claim(key)) == (True, False)


def should_grant_the_claim_again_when_it_was_released(adapters):
    key = f"k-{uuid.uuid4().hex}"
    adapters["claims"].try_claim(key)
    adapters["claims"].release(key)
    assert adapters["claims"].try_claim(key) is True


def should_not_fail_when_a_missing_claim_is_released(adapters):
    adapters["claims"].release(f"k-{uuid.uuid4().hex}")


def should_keep_claims_independent_when_keys_differ(adapters):
    a, b = f"k-{uuid.uuid4().hex}", f"k-{uuid.uuid4().hex}"
    assert (adapters["claims"].try_claim(a), adapters["claims"].try_claim(b)) == (True, True)


# --- ConversationStore ------------------------------------------------------------------

def turns(count):
    return [ConversationTurn(Role.ELDER, f"m{i}", taipei(8, i)) for i in range(count)]


def should_return_the_latest_turns_oldest_first_when_a_limit_is_given(adapters, elder_id):
    repo = adapters["conversations"]
    for turn in turns(5):
        repo.append(elder_id, turn)
    assert [t.text for t in repo.recent(elder_id, 3)] == ["m2", "m3", "m4"]


def should_return_an_empty_list_when_the_elder_has_no_turns(adapters, elder_id):
    assert adapters["conversations"].recent(elder_id, 10) == []


def should_keep_turn_fields_when_a_turn_is_stored(adapters, elder_id):
    original = ConversationTurn(Role.AGENT, "早安，王奶奶", taipei(8, 0))
    adapters["conversations"].append(elder_id, original)
    assert adapters["conversations"].recent(elder_id, 1) == [original]
