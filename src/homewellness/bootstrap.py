"""Wiring. It builds the real objects and gives them to the controllers.

This is the only module that knows which store, clock and notifier are in use.
"""

import logging
from collections import deque
from dataclasses import dataclass, field

from homewellness.controllers.mqtt import MqttController
from homewellness.controllers.telemetry import TelemetryController
from homewellness.demo import demo_profile
from homewellness.interfaces import Clock
from homewellness.models.trigger_policy import ProactiveTrigger
from homewellness.services.clock import SimulatedClock, SystemClock
from homewellness.services.notifier import RecordingNotifier
from homewellness.settings import Settings
from homewellness.stores.dynamodb import stores as dynamo
from homewellness.stores.dynamodb.table import DynamoTable
from homewellness.stores.memory import (
    InMemoryClaimStore,
    InMemoryElderStore,
    InMemoryIntakeStore,
    InMemoryTelemetryStore,
)

logger = logging.getLogger("homewellness.worker")


@dataclass
class Container:
    settings: Settings
    clock: Clock
    telemetry: TelemetryController
    mqtt: MqttController
    notifier: RecordingNotifier
    # The newest proactive triggers. Phase 3 hands them to the agent.
    triggers: deque = field(default_factory=lambda: deque(maxlen=100))

    def record_trigger(self, elder_id: str, trigger: ProactiveTrigger) -> None:
        self.triggers.append((elder_id, trigger))


def build_container(settings: Settings, *, clock: Clock | None = None) -> Container:
    base_clock = clock or SystemClock()
    # In demo mode the scenario can move the clock. Otherwise the clock stays real.
    demo_clock = SimulatedClock(base_clock) if settings.demo_mode else None
    active_clock = demo_clock or base_clock

    if settings.store_backend == "dynamodb":
        table = DynamoTable(
            settings.dynamodb_table, endpoint_url=settings.dynamodb_endpoint,
            region_name=settings.aws_region,
        )
        table.ensure_table()  # Retries while DynamoDB Local starts.
        telemetry_store = dynamo.DynamoTelemetryStore(table)
        intakes, claims = dynamo.DynamoIntakeStore(table), dynamo.DynamoClaimStore(table)
    else:
        telemetry_store = InMemoryTelemetryStore()
        intakes, claims = InMemoryIntakeStore(), InMemoryClaimStore()

    telemetry = TelemetryController(
        elders=InMemoryElderStore([demo_profile()]), telemetry=telemetry_store,
        intakes=intakes, claims=claims, clock=active_clock,
    )
    holder: list[Container] = []
    mqtt_controller = MqttController(
        telemetry=telemetry,
        on_trigger=lambda elder_id, trigger: holder[0].record_trigger(elder_id, trigger),
        clock_control=demo_clock,
    )
    container = Container(settings, active_clock, telemetry, mqtt_controller, RecordingNotifier())
    holder.append(container)
    return container
