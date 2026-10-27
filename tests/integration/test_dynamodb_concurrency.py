"""Concurrency against a real DynamoDB endpoint. Ten callers race for one result."""

import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

from builders import TODAY, make_profile, make_vitals, taipei
from homewellness.controllers.escalation import EscalationController, EscalationStatus
from homewellness.controllers.telemetry import TelemetryController
from homewellness.models.medication import MedicationIntake
from homewellness.models.symptoms import Symptom
from homewellness.services.clock import FixedClock
from homewellness.services.notifier import RecordingNotifier
from homewellness.stores.dynamodb import stores as dynamo
from homewellness.stores.memory import InMemoryElderStore

pytestmark = [pytest.mark.integration, pytest.mark.concurrency]


def race(function, count=10):
    with ThreadPoolExecutor(max_workers=count) as pool:
        return list(pool.map(lambda _: function(), range(count)))


def should_grant_one_claim_when_ten_callers_use_the_same_key(dynamo_table):
    claims = dynamo.DynamoClaimStore(dynamo_table)
    key = f"race-{uuid.uuid4().hex}"
    assert race(lambda: claims.try_claim(key)).count(True) == 1


def should_store_one_intake_when_ten_confirmations_race(dynamo_table, elder_id):
    intakes = dynamo.DynamoIntakeStore(dynamo_table)
    item = MedicationIntake(elder_id, "am", TODAY, taipei(8, 5))
    assert race(lambda: intakes.add(item)).count(True) == 1
    assert len(intakes.list_for_date(elder_id, TODAY)) == 1


def should_send_one_alert_when_ten_escalations_use_the_same_key(dynamo_table, elder_id):
    telemetry = dynamo.DynamoTelemetryStore(dynamo_table)
    telemetry.save_vitals(make_vitals(taipei(12, 0), 188, 121, elder_id))
    notifier = RecordingNotifier()
    controller = EscalationController(
        elders=InMemoryElderStore([make_profile(elder_id)]), telemetry=telemetry,
        claims=dynamo.DynamoClaimStore(dynamo_table), notifier=notifier,
        clock=FixedClock(taipei(12, 5)),
    )
    symptoms = frozenset({Symptom.CHEST_PAIN})
    statuses = [o.status for o in race(lambda: controller.escalate(elder_id, symptoms, "same-key"))]
    assert statuses.count(EscalationStatus.SENT) == 1
    assert statuses.count(EscalationStatus.DUPLICATE) == 9
    assert len(notifier.sent) == 1


def should_return_each_trigger_once_when_ten_ticks_race(dynamo_table, elder_id):
    controller = TelemetryController(
        elders=InMemoryElderStore([make_profile(elder_id)]),
        telemetry=dynamo.DynamoTelemetryStore(dynamo_table),
        intakes=dynamo.DynamoIntakeStore(dynamo_table),
        claims=dynamo.DynamoClaimStore(dynamo_table), clock=FixedClock(taipei(8, 5)),
    )
    results = race(lambda: controller.ingest(elder_id))
    assert sum(len(r) for r in results) == 1
