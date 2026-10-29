"""FastAPI application: trace-id, access log and sanitized errors."""

import http
import logging
import re
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from homewellness.api.routes import router
from homewellness.models.errors import (
    AgentUnavailableError,
    DomainError,
    DuplicateRequestError,
    ElderNotFoundError,
    IdempotencyKeyError,
)
from homewellness.observability import bind_context, current_trace_id, new_trace_id

logger = logging.getLogger("homewellness.api")
_ELDER_IN_PATH = re.compile(r"^/elders/([A-Za-z0-9_-]{1,64})(?:/|$)")


def _error(status: int, code: str, message: str, fields: list[dict[str, str]] | None = None):
    body: dict[str, Any] = {"code": code, "message": message, "trace_id": current_trace_id()}
    if fields:
        body["fields"] = fields
    return JSONResponse(status_code=status, content={"error": body})


def _describe(error: DomainError) -> tuple[int, str, str]:
    """Return status, code and a public message. The message never repeats the input."""
    if isinstance(error, ElderNotFoundError):
        return 404, "elder_not_found", "Elder not found."
    if isinstance(error, DuplicateRequestError):
        return 409, "duplicate_request", "This request was already handled."
    if isinstance(error, IdempotencyKeyError):
        return 400, "invalid_idempotency_key", str(error)  # Our own fixed text.
    if isinstance(error, AgentUnavailableError):
        return 503, "agent_unavailable", "The assistant is not available. Try again."
    return 422, "invalid_request", "The request is not valid."


def create_app(container: Any, *, subscriber: Any = None, publisher: Any = None) -> FastAPI:
    """`subscriber`: start, stop, is_ready. `publisher`: publish. Both are optional."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if subscriber is not None:
            subscriber.start()
        try:
            yield
        finally:
            if subscriber is not None:
                subscriber.stop()
            if publisher is not None and hasattr(publisher, "close"):
                publisher.close()

    app = FastAPI(title="HomeWellness Companion API", version="0.3.0", lifespan=lifespan)
    app.state.container = container
    app.state.subscriber = subscriber
    app.state.publisher = publisher
    app.include_router(router)

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, error: DomainError):
        status, code, message = _describe(error)
        return _error(status, code, message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, error: RequestValidationError):
        # Only the field name and the error type. Never the input value.
        fields = [{"field": ".".join(str(p) for p in e["loc"]), "problem": e["type"]}
                  for e in error.errors()]
        return _error(422, "validation_error", "The request is not valid.", fields)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, error: StarletteHTTPException):
        phrase = http.HTTPStatus(error.status_code).phrase
        code = "not_found" if error.status_code == 404 else "http_error"
        return _error(error.status_code, code, phrase + ".")

    @app.middleware("http")
    async def trace_requests(request: Request, call_next):
        match = _ELDER_IN_PATH.match(request.url.path)
        trace_id = new_trace_id()  # A new trace-id starts at every request.
        with bind_context(trace_id=trace_id, user_id=match.group(1) if match else "-"):
            started = time.perf_counter()
            try:
                response = await call_next(request)
            except Exception as error:  # noqa: BLE001 - last line of defense
                logger.error("unhandled error", exc_info=True, extra={
                    "event": "unhandled_error", "error_type": type(error).__name__})
                response = _error(500, "internal_error", "Internal error.")
            response.headers["X-Trace-Id"] = trace_id
            logger.info("request", extra={
                "event": "request", "method": request.method, "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            })
            return response

    return app
