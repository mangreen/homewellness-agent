"""Run the agent with LangChain. The model can be the scripted stand-in or a real LLM."""

import json
import logging
from typing import Literal

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.tools import tool

from homewellness.interfaces import AgentActions
from homewellness.models.errors import AgentUnavailableError
from homewellness.models.interaction import AgentRequest, Role

logger = logging.getLogger("homewellness.agent")

# One answer needs at most: model, tool, model, tool, model. The rest is a safety margin.
_RECURSION_LIMIT = 12

SymptomName = Literal["dizziness", "chest_pain", "shortness_of_breath", "fainting"]


def _json(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False)


def _build_tools(elder_id: str, actions: AgentActions) -> list:
    """Tools for ONE elder. The model cannot choose another elder: no tool takes an id."""

    @tool
    def get_latest_vitals() -> str:
        """Read the newest blood pressure and heart rate from the elder's wristband.
        Use it when the elder says that she feels unwell, for example dizzy."""
        return _json(actions.get_latest_vitals(elder_id))

    @tool
    def get_medication_status() -> str:
        """Read the medicine schedule and the state of each dose today."""
        return _json(actions.get_medication_status(elder_id))

    @tool
    def log_medication_intake() -> str:
        """Record that the elder says she took her medicine now."""
        return _json(actions.log_medication_intake(elder_id))

    @tool
    def escalate_emergency(symptoms: list[SymptomName]) -> str:
        """Ask the safety policy to alert the family or the emergency services.
        The policy decides from the latest vitals and the symptoms. It can refuse."""
        return _json(actions.escalate_emergency(elder_id, list(symptoms)))

    return [get_latest_vitals, get_medication_status, log_medication_intake, escalate_emergency]


def _to_messages(request: AgentRequest) -> list[BaseMessage]:
    messages: list[BaseMessage] = [
        HumanMessage(turn.text) if turn.role is Role.ELDER else AIMessage(turn.text)
        for turn in request.history
    ]
    messages.append(HumanMessage(request.message))
    return messages


class LangChainAgentRunner:
    def __init__(self, model: BaseChatModel, actions: AgentActions) -> None:
        self._model = model
        self._actions = actions

    def reply(self, request: AgentRequest) -> str:
        try:
            agent = create_agent(
                self._model, tools=_build_tools(request.elder_id, self._actions),
                system_prompt=request.system_prompt,
            )
            result = agent.invoke(
                {"messages": _to_messages(request)}, config={"recursion_limit": _RECURSION_LIMIT}
            )
            content = result["messages"][-1].content
        except Exception as error:
            # NOTE: Log the error type only. Messages can hold personal data.
            logger.error("agent failed", extra={"event": "agent_failed",
                                                "error_type": type(error).__name__})
            raise AgentUnavailableError("the agent could not answer") from error
        text = content if isinstance(content, str) else "".join(
            block.get("text", "") for block in content if isinstance(block, dict)
        )
        if not text.strip():
            raise AgentUnavailableError("the agent returned an empty answer")
        return text
