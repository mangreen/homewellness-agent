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
