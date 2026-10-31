"""Domain errors. Each error means a business rule was broken."""


class DomainError(ValueError):
    """Base class for all domain errors."""


class InvalidVitalsError(DomainError):
    """A health measurement is not valid."""


class InvalidScheduleError(DomainError):
    """A medication schedule or elder profile is not valid."""


class ElderNotFoundError(DomainError):
    """No elder exists with the given id."""


class EmptyMessageError(DomainError):
    """The elder message has no text."""


class DuplicateRequestError(DomainError):
    """The same request was already handled (same idempotency key)."""


class IdempotencyKeyError(DomainError):
    """The idempotency key is missing or has a bad format."""


class AgentUnavailableError(DomainError):
    """The agent could not produce an answer.

    `detail` explains why (for the evaluation tool). It is never sent to an API client.
    """

    def __init__(self, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.detail = detail
