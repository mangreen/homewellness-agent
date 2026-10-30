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
    assert FallbackAgentRunner(primary, backup, lambda: events.append(1)).reply(REQUEST) == "real"
    assert (backup.calls, events) == (0, [])


def should_use_the_backup_and_tell_the_observer_when_the_primary_is_unavailable():
    primary = Runner(error=AgentUnavailableError("down"))
    backup, events = Runner("offline"), []
    reply = FallbackAgentRunner(primary, backup, lambda: events.append(1)).reply(REQUEST)
    assert (reply, backup.calls, events) == ("offline", 1, [1])


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
