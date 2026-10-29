"""Wiring. It builds the real objects and gives them to the controllers.

This is the only module that knows which store, clock, notifier and LLM are in use.
"""

import logging
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from langchain_core.language_models.chat_models import BaseChatModel

from homewellness.controllers.agent_actions import AgentActionsController
from homewellness.controllers.chat import ChatController
from homewellness.controllers.escalation import EscalationController
from homewellness.controllers.medication import MedicationController
from homewellness.controllers.mqtt import MqttController
from homewellness.controllers.telemetry import TelemetryController
from homewellness.demo import demo_profile
from homewellness.interfaces import ClaimStore, Clock
from homewellness.models.trigger_policy import ProactiveTrigger
from homewellness.services.agent import LangChainAgentRunner
from homewellness.services.clock import SimulatedClock, SystemClock
from homewellness.services.notifier import RecordingNotifier
from homewellness.services.scripted_model import ScriptedChatModel
from homewellness.settings import Settings
from homewellness.stores.dynamodb import stores as dynamo
from homewellness.stores.dynamodb.table import DynamoTable
from homewellness.stores.memory import (
    InMemoryClaimStore,
    InMemoryConversationStore,
    InMemoryElderStore,
    InMemoryIntakeStore,
    InMemoryTelemetryStore,
)

logger = logging.getLogger("homewellness.app")


@dataclass
class Container:
    settings: Settings
    clock: Clock
    telemetry: TelemetryController
    medication: MedicationController
    escalation: EscalationController
    actions: AgentActionsController
    chat: ChatController
    mqtt: MqttController
    notifier: RecordingNotifier
    claims: ClaimStore
    # The newest proactive triggers, kept for the demo views.
    triggers: deque = field(default_factory=lambda: deque(maxlen=100))

    def handle_triggers(self, elder_id: str, triggers: Sequence[ProactiveTrigger]) -> None:
        """Device event -> the agent starts the conversation."""
        for trigger in triggers:
            self.triggers.append((elder_id, trigger))
        try:
            self.chat.proactive(elder_id, triggers)
        except Exception:  # noqa: BLE001 - a failed greeting must not stop the ingest
            logger.exception("proactive message failed", extra={"event": "proactive_failed"})


def _build_model(settings: Settings) -> BaseChatModel:
    if settings.llm_provider == "fake":
        return ScriptedChatModel()
    # NOTE: Add a real provider here, for example Amazon Bedrock. No controller changes.
    raise ValueError(f"LLM_PROVIDER {settings.llm_provider!r} is not implemented")


def build_container(
    settings: Settings,
    *,
    clock: Clock | None = None,
    on_tool_call: Callable[[str, str], None] | None = None,
) -> Container:
    model = _build_model(settings)
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
        conversations = dynamo.DynamoConversationStore(table)
    else:
        telemetry_store = InMemoryTelemetryStore()
        intakes, claims = InMemoryIntakeStore(), InMemoryClaimStore()
        conversations = InMemoryConversationStore()

    elders = InMemoryElderStore([demo_profile()])
    notifier = RecordingNotifier()
    medication = MedicationController(elders=elders, intakes=intakes, clock=active_clock)
    escalation = EscalationController(
        elders=elders, telemetry=telemetry_store, claims=claims, notifier=notifier,
        clock=active_clock,
    )
    actions = AgentActionsController(
        elders=elders, telemetry=telemetry_store, intakes=intakes, medication=medication,
        escalation=escalation, clock=active_clock, on_call=on_tool_call,
    )
    chat = ChatController(
        elders=elders, telemetry=telemetry_store, intakes=intakes, conversations=conversations,
        agent=LangChainAgentRunner(model, actions), clock=active_clock,
    )
    telemetry = TelemetryController(
        elders=elders, telemetry=telemetry_store, intakes=intakes, claims=claims,
        clock=active_clock,
    )
    holder: list[Container] = []
    mqtt_controller = MqttController(
        telemetry=telemetry,
        on_triggers=lambda elder_id, triggers: holder[0].handle_triggers(elder_id, triggers),
        clock_control=demo_clock,
    )
    container = Container(
        settings, active_clock, telemetry, medication, escalation, actions, chat,
        mqtt_controller, notifier, claims,
    )
    holder.append(container)
    return container
