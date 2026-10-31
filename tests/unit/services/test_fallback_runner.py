import httpx
import openai
import pytest

from builders import make_health_context
from homewellness.models.errors import AgentUnavailableError
from homewellness.models.interaction import AgentRequest
from homewellness.services.agent import FallbackAgentRunner

REQUEST = AgentRequest("e1", "hi", make_health_context("e1"), (), "")


class Runner:
    def __init__(self, answer=None, error=None):
        self.answer, self.error, self.calls = answer, error, 0

    def reply(self, request):
        self.calls += 1
        if self.error:
            raise self.error
        return self.answer


def should_use_the_primary_answer_when_it_works():
    primary, backup, events = Runner("real"), Runner("offline"), []
    assert FallbackAgentRunner(primary, backup, events.append).reply(REQUEST) == "real"
    assert (backup.calls, events) == (0, [])


def should_use_the_backup_and_tell_the_observer_when_the_primary_is_unavailable():
    primary = Runner(error=AgentUnavailableError("down"))
    backup, events = Runner("offline"), []
    reply = FallbackAgentRunner(primary, backup, events.append).reply(REQUEST)
    assert (reply, backup.calls, events) == ("offline", 1, ["unknown"])


def should_work_without_an_observer():
    runner = FallbackAgentRunner(Runner(error=AgentUnavailableError("x")), Runner("offline"))
    assert runner.reply(REQUEST) == "offline"


def should_raise_when_the_backup_fails_too():
    runner = FallbackAgentRunner(Runner(error=AgentUnavailableError("a")),
                                 Runner(error=AgentUnavailableError("b")))
    with pytest.raises(AgentUnavailableError):
        runner.reply(REQUEST)


def should_not_hide_an_unexpected_error_of_the_primary():
    runner = FallbackAgentRunner(Runner(error=KeyError("bug")), Runner("offline"))
    with pytest.raises(KeyError):
        runner.reply(REQUEST)


def should_tell_the_error_type_and_the_status_but_not_the_message():
    response = httpx.Response(404, request=httpx.Request("POST", "https://x/v1"))
    cause = openai.NotFoundError("secret detail", response=response, body=None)
    error = AgentUnavailableError("down")
    error.__cause__ = cause
    events = []
    FallbackAgentRunner(Runner(error=error), Runner("offline"), events.append).reply(REQUEST)
    assert events == ["NotFoundError, HTTP 404"] and "secret" not in events[0]
