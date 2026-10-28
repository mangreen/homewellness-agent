"""Controller: talk with the elder through the agent."""

from collections.abc import Sequence

from homewellness.controllers.health_context import build_health_context
from homewellness.interfaces import (
    AgentRunner,
    Clock,
    ConversationStore,
    ElderStore,
    IntakeStore,
    TelemetryStore,
)
from homewellness.models.errors import EmptyMessageError
from homewellness.models.interaction import (
    AgentRequest,
    ConversationTurn,
    HealthContext,
    Role,
)
from homewellness.models.trigger_policy import ProactiveTrigger
from homewellness.views.agent_prompts import render_event_message, render_system_prompt

# NOTE: Short history keeps the agent focused and the prompt small.
HISTORY_LIMIT = 10


class ChatController:
    def __init__(
        self,
        *,
        elders: ElderStore,
        telemetry: TelemetryStore,
        intakes: IntakeStore,
        conversations: ConversationStore,
        agent: AgentRunner,
        clock: Clock,
    ) -> None:
        self._elders = elders
        self._telemetry = telemetry
        self._intakes = intakes
        self._conversations = conversations
        self._agent = agent
        self._clock = clock

    def status(self, elder_id: str) -> HealthContext:
        return build_health_context(
            profile=self._elders.get(elder_id), telemetry=self._telemetry,
            intakes=self._intakes, now=self._clock.now(),
        )

    def history(self, elder_id: str, limit: int = HISTORY_LIMIT) -> list[ConversationTurn]:
        self._elders.get(elder_id)  # Raises if the elder does not exist.
        return self._conversations.recent(elder_id, limit)

    def _ask(self, elder_id: str, message: str) -> str:
        context = self.status(elder_id)
        history = tuple(self._conversations.recent(elder_id, HISTORY_LIMIT))
        request = AgentRequest(elder_id, message, context, history, render_system_prompt(context))
        return self._agent.reply(request)

    def _remember(self, elder_id: str, role: Role, text: str) -> None:
        self._conversations.append(elder_id, ConversationTurn(role, text, self._clock.now()))

    def reply(self, elder_id: str, text: str) -> str:
        message = text.strip()
        if not message:
            raise EmptyMessageError("message has no text")
        answer = self._ask(elder_id, message)
        # Store the turns only after the agent succeeds.
        self._remember(elder_id, Role.ELDER, message)
        self._remember(elder_id, Role.AGENT, answer)
        return answer

    def proactive(self, elder_id: str, triggers: Sequence[ProactiveTrigger]) -> str | None:
        """The agent starts the conversation after a device event."""
        if not triggers:
            return None
        medication = self._elders.get(elder_id).medication_schedule.medication_name
        answer = self._ask(elder_id, render_event_message(triggers, medication))
        self._remember(elder_id, Role.AGENT, answer)
        return answer
