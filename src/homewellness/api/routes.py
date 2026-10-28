"""HTTP controllers. Each route validates the input and calls one controller method."""

import re
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse

from homewellness.api.schemas import (
    AlertOut,
    AlertsResponse,
    ConversationResponse,
    DoseOut,
    ErrorResponse,
    MessageRequest,
    MessageResponse,
    ScenarioName,
    ScenarioResponse,
    StatusResponse,
    TurnOut,
)
from homewellness.controllers.idempotency import idempotent
from homewellness.demo import DEMO_ELDER_ID
from homewellness.models.errors import IdempotencyKeyError
from homewellness.observability import current_trace_id
from homewellness.simulator.scenarios import build_scenario

router = APIRouter()

_KEY_FORMAT = re.compile(r"^[A-Za-z0-9._:-]{8,64}$")
_TAIPEI = ZoneInfo("Asia/Taipei")
ElderId = Annotated[str, Path(pattern=r"^[A-Za-z0-9_-]{1,64}$")]
_ERRORS = {code: {"model": ErrorResponse} for code in (400, 404, 409, 422, 500, 503)}


def idempotency_key(
    key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", description="Unique per request. 8-64 safe characters."),
    ] = None,
) -> str:
    if key is None:
        raise IdempotencyKeyError("the Idempotency-Key header is required")
    if not _KEY_FORMAT.match(key):
        raise IdempotencyKeyError("the Idempotency-Key header has a bad format")
    return key


IdemKey = Annotated[str, Depends(idempotency_key)]


def _container(request: Request):
    return request.app.state.container


@router.get("/healthz", tags=["system"])
def healthz(request: Request) -> JSONResponse:
    subscriber = request.app.state.subscriber
    ready = subscriber is None or subscriber.is_ready()
    status = {"status": "ok" if ready else "starting"}
    return JSONResponse(status, status_code=200 if ready else 503)


@router.post("/elders/{elder_id}/messages", response_model=MessageResponse, responses=_ERRORS,
             tags=["chat"])
def post_message(elder_id: ElderId, body: MessageRequest, request: Request,
                 key: IdemKey) -> MessageResponse:
    container = _container(request)
    with idempotent(container.claims, f"message:{elder_id}", key):
        reply = container.chat.reply(elder_id, body.text)
    return MessageResponse(reply=reply, trace_id=current_trace_id())


@router.get("/elders/{elder_id}/conversation", response_model=ConversationResponse,
            responses=_ERRORS, tags=["chat"])
def get_conversation(elder_id: ElderId, request: Request,
                     limit: Annotated[int, Query(ge=1, le=50)] = 20) -> ConversationResponse:
    turns = _container(request).chat.history(elder_id, limit)
    return ConversationResponse(
        turns=[TurnOut(role=t.role.value, text=t.text, at=t.at) for t in turns]
    )


@router.get("/elders/{elder_id}/status", response_model=StatusResponse, responses=_ERRORS,
            tags=["chat"])
def get_status(elder_id: ElderId, request: Request) -> StatusResponse:
    context = _container(request).chat.status(elder_id)
    vitals = context.vitals
    return StatusResponse(
        display_name=context.display_name,
        local_time=f"{context.local_now:%H:%M}",
        blood_pressure=str(vitals.blood_pressure) if vitals and vitals.blood_pressure else None,
        alert_level=context.alert_level.value if context.alert_level else None,
        heart_rate_bpm=vitals.heart_rate_bpm if vitals else None,
        sleep_hours=context.sleep.hours_asleep if context.sleep else None,
        doses=[DoseOut(dose_id=s.dose.dose_id, label=s.dose.label,
                       time=f"{s.dose.time_of_day:%H:%M}", state=s.state.value)
               for s in context.doses],
    )


@router.get("/alerts", response_model=AlertsResponse, tags=["alerts"])
def get_alerts(request: Request) -> AlertsResponse:
    sent = _container(request).notifier.list_sent()
    return AlertsResponse(alerts=[
        AlertOut(action=n.action.value, title=n.title, body=n.body,
                 recipients=[r.value for r in n.recipients], created_at=n.created_at)
        for n in sent
    ])


@router.post("/sim/scenarios/{name}", response_model=ScenarioResponse, responses=_ERRORS,
             tags=["demo"])
def run_scenario(name: ScenarioName, request: Request, key: IdemKey) -> ScenarioResponse:
    """Demo only. Publishes the device messages of a scenario to MQTT."""
    container = _container(request)
    publisher = request.app.state.publisher
    if not container.settings.demo_mode or publisher is None:
        raise HTTPException(status_code=404)
    with idempotent(container.claims, f"scenario:{name}", key):
        messages = build_scenario(name, DEMO_ELDER_ID, datetime.now(_TAIPEI).date())
        for message in messages:
            publisher.publish(message.topic, message.body())
    return ScenarioResponse(scenario=name, published=len(messages))
