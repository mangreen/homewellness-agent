"""Wiring. It builds the real objects and gives them to the controllers.

This is the only module that knows which store, clock, notifier and LLM are in use.
"""

import logging
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from homewellness.controllers.agent_actions import AgentActionsController
from homewellness.controllers.chat import ChatController
from homewellness.controllers.escalation import EscalationController
from homewellness.controllers.medication import MedicationController
from homewellness.controllers.mqtt import MqttController
from homewellness.controllers.telemetry import TelemetryController
from homewellness.demo import demo_profile
from homewellness.interfaces import ClaimStore, Clock
from homewellness.models.interaction import Notification
from homewellness.models.trigger_policy import ProactiveTrigger, TriggerKind
from homewellness.services.activity import ActivityLog
from homewellness.services.agent import FallbackAgentRunner, LangChainAgentRunner
from homewellness.services.clock import SimulatedClock, SystemClock
from homewellness.services.llm_factory import BrainInfo, build_chat_model, describe_brain
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

_TRIGGER_TEXT = {
    TriggerKind.ABNORMAL_VITALS: "血壓異常",
    TriggerKind.MEDICATION_DUE: "該吃藥",
    TriggerKind.POOR_SLEEP: "睡眠不足",
}


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
    activity: ActivityLog
    reset_state: Callable[[], None]  # Forget stored data and move the demo clock back.
    brain: BrainInfo
    # The newest proactive triggers, kept for the demo views.
    triggers: deque = field(default_factory=lambda: deque(maxlen=100))

    def handle_triggers(self, elder_id: str, triggers: Sequence[ProactiveTrigger]) -> None:
        """Device event -> the agent starts the conversation."""
        for trigger in triggers:
            self.triggers.append((elder_id, trigger))
            self.activity.add("trigger", f"主動觸發：{_TRIGGER_TEXT[trigger.kind]}")
        try:
            self.chat.proactive(elder_id, triggers)
        except Exception:  # noqa: BLE001 - a failed greeting must not stop the ingest
            logger.exception("proactive message failed", extra={"event": "proactive_failed"})

    def reset(self) -> None:
        """Start the demo story again. For the demo only."""
        self.reset_state()
        self.notifier.clear()
        self.triggers.clear()
        self.activity.clear()


def build_container(
    settings: Settings,
    *,
    clock: Clock | None = None,
    on_tool_call: Callable[[str, str], None] | None = None,
) -> Container:
    model = build_chat_model(settings)  # Fails at start-up when a key is missing.
    brain = describe_brain(settings)
    base_clock = clock or SystemClock()
    # In demo mode the scenario can move the clock. Otherwise the clock stays real.
    demo_clock = SimulatedClock(base_clock) if settings.demo_mode else None
    active_clock = demo_clock or base_clock
    activity = ActivityLog(active_clock)

    if settings.store_backend == "dynamodb":
        table = DynamoTable(
            settings.dynamodb_table, endpoint_url=settings.dynamodb_endpoint,
            region_name=settings.aws_region,
        )
        table.ensure_table()  # Retries while DynamoDB Local starts.
        telemetry_store = dynamo.DynamoTelemetryStore(table)
        intakes, claims = dynamo.DynamoIntakeStore(table), dynamo.DynamoClaimStore(table)
        conversations = dynamo.DynamoConversationStore(table)
        forget_data: Callable[[], None] = table.reset
    else:
        telemetry_store = InMemoryTelemetryStore()
        intakes, claims = InMemoryIntakeStore(), InMemoryClaimStore()
        conversations = InMemoryConversationStore()

        def forget_data() -> None:
            for store in (telemetry_store, intakes, claims, conversations):
                store.clear()

    def reset_state() -> None:
        forget_data()
        if demo_clock is not None:
            demo_clock.reset()

    def on_alert(notification: Notification) -> None:
        recipients = ", ".join(r.value for r in notification.recipients)
        activity.add("alert", f"警報 {notification.action.value} → {recipients}")

    def observe_tool(tool: str, elder_id: str) -> None:
        activity.add("tool", f"Agent 呼叫工具：{tool}")
        if on_tool_call is not None:
            on_tool_call(tool, elder_id)

    elders = InMemoryElderStore([demo_profile()])
    notifier = RecordingNotifier(on_send=on_alert)
    medication = MedicationController(elders=elders, intakes=intakes, clock=active_clock)
    escalation = EscalationController(
        elders=elders, telemetry=telemetry_store, claims=claims, notifier=notifier,
        clock=active_clock,
    )
    actions = AgentActionsController(
        elders=elders, telemetry=telemetry_store, intakes=intakes, medication=medication,
        escalation=escalation, clock=active_clock, on_call=observe_tool,
    )
    agent = LangChainAgentRunner(model, actions)
    if brain.external and brain.fallback:
        agent = FallbackAgentRunner(
            agent, LangChainAgentRunner(ScriptedChatModel(), actions),
            on_fallback=lambda: activity.add("llm", "外部 LLM 暫時無法使用，改用離線模型"),
        )
    chat = ChatController(
        elders=elders, telemetry=telemetry_store, intakes=intakes, conversations=conversations,
        agent=agent, clock=active_clock,
    )
    telemetry = TelemetryController(
        elders=elders, telemetry=telemetry_store, intakes=intakes, claims=claims,
        clock=active_clock,
    )
    holder: list[Container] = []
    mqtt_controller = MqttController(
        telemetry=telemetry,
        on_triggers=lambda elder_id, triggers: holder[0].handle_triggers(elder_id, triggers),
        on_event=activity.add,
        clock_control=demo_clock,
    )
    container = Container(
        settings, active_clock, telemetry, medication, escalation, actions, chat,
        mqtt_controller, notifier, claims, activity, reset_state, brain,
    )
    holder.append(container)
    return container
