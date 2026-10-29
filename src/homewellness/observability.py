"""Structured JSON logs with trace-id and user-id.

The context is stored in context variables. Every layer below the entry point
logs the same trace-id without passing it as an argument.
"""

import json
import logging
import sys
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime

_trace_id: ContextVar[str] = ContextVar("trace_id", default="-")
_user_id: ContextVar[str] = ContextVar("user_id", default="-")

# Attributes of a plain LogRecord. Everything else is an event field set with `extra=`.
_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


def new_trace_id() -> str:
    return uuid.uuid4().hex


@contextmanager
def bind_context(*, trace_id: str, user_id: str = "-") -> Iterator[None]:
    trace_token = _trace_id.set(trace_id)
    user_token = _user_id.set(user_id)
    try:
        yield
    finally:
        _trace_id.reset(trace_token)
        _user_id.reset(user_token)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "trace_id": _trace_id.get(),
            "user_id": _user_id.get(),
        }
        entry.update({k: v for k, v in record.__dict__.items() if k not in _RESERVED})
        if record.exc_info and record.exc_info[0] is not None:
            # NOTE: Log the error type only. Messages and stack traces can hold personal data.
            entry["error_type"] = record.exc_info[0].__name__
        return json.dumps(entry, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
