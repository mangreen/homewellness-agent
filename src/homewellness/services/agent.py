"""Run the agent with LangChain. The model can be the scripted stand-in or a real LLM."""

import json
import logging
from collections.abc import Callable
from typing import Literal

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.tools import tool

from homewellness.interfaces import AgentActions, AgentRunner
from homewellness.models.errors import AgentUnavailableError
from homewellness.models.interaction import AgentRequest, Role
from homewellness.services.llm_errors import explain_llm_error

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
            # NOTE: Log the error type and the status only. Messages can hold personal data.
            logger.error("agent failed", extra={
                "event": "agent_failed", "error_type": type(error).__name__,
                "status_code": getattr(error, "status_code", None)})
            raise AgentUnavailableError(
                "the agent could not answer", detail=explain_llm_error(error)
            ) from error
        text = content if isinstance(content, str) else "".join(
            block.get("text", "") for block in content if isinstance(block, dict)
        )
        if not text.strip():
            raise AgentUnavailableError("the agent returned an empty answer")
        return text


def _short_reason(cause: BaseException | None) -> str:
    """The error type and the HTTP status. Never the message: it can hold personal data."""
    if cause is None:
        return "unknown"
    status = getattr(cause, "status_code", None)
    return f"{type(cause).__name__}, HTTP {status}" if status else type(cause).__name__


class FallbackAgentRunner:
    """Ask the primary runner. If it is unavailable, ask the backup (the offline model).

    NOTE: The primary may have run a tool before it failed. The tools are idempotent,
    so the backup repeats them safely: no second intake and no second alert.
    """

    def __init__(
        self,
        primary: AgentRunner,
        backup: AgentRunner,
        on_fallback: Callable[[str], None] | None = None,  # Gets a short reason.
    ) -> None:
        self._primary = primary
        self._backup = backup
        self._on_fallback = on_fallback

    def reply(self, request: AgentRequest) -> str:
        try:
            return self._primary.reply(request)
        except AgentUnavailableError as error:
            reason = _short_reason(error.__cause__)
            logger.warning("llm fallback", extra={"event": "llm_fallback", "reason": reason})
            if self._on_fallback is not None:
                self._on_fallback(reason)
            return self._backup.reply(request)
