"""Use case: answer a message from the elder through the agent."""

from homewellness.application.health_context import build_health_context
from homewellness.application.models import AgentRequest, ConversationTurn, Role
from homewellness.application.ports import (
    AgentRunner,
    Clock,
    ConversationRepository,
    ElderRepository,
    IntakeRepository,
    TelemetryRepository,
)
from homewellness.domain.errors import EmptyMessageError

# NOTE: Short history keeps the agent focused and the prompt small.
HISTORY_LIMIT = 10


class HandleElderMessage:
    def __init__(
        self,
        *,
        elders: ElderRepository,
        telemetry: TelemetryRepository,
        intakes: IntakeRepository,
        conversations: ConversationRepository,
        agent: AgentRunner,
        clock: Clock,
    ) -> None:
        self._elders = elders
        self._telemetry = telemetry
        self._intakes = intakes
        self._conversations = conversations
        self._agent = agent
        self._clock = clock

    def execute(self, elder_id: str, text: str) -> str:
        message = text.strip()
        if not message:
            raise EmptyMessageError("message has no text")
        profile = self._elders.get(elder_id)
        context = build_health_context(
            profile=profile, telemetry=self._telemetry, intakes=self._intakes,
            now=self._clock.now(),
        )
        history = tuple(self._conversations.recent(elder_id, HISTORY_LIMIT))
        reply = self._agent.reply(AgentRequest(elder_id, message, context, history))
        # Store the turns only after the agent succeeds.
        elder_turn = ConversationTurn(Role.ELDER, message, self._clock.now())
        agent_turn = ConversationTurn(Role.AGENT, reply, self._clock.now())
        self._conversations.append(elder_id, elder_turn)
        self._conversations.append(elder_id, agent_turn)
        return reply
