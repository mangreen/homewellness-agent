"""HTTP data shapes. They are the JSON view of the models."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

ScenarioName = Literal["morning", "dizzy", "crisis"]


class MessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")  # Reject unknown fields.

    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class MessageResponse(BaseModel):
    reply: str
    trace_id: str


class TurnOut(BaseModel):
    role: str
    text: str
    at: datetime


class ConversationResponse(BaseModel):
    turns: list[TurnOut]


class DoseOut(BaseModel):
    dose_id: str
    label: str
    time: str
    state: str


class StatusResponse(BaseModel):
    display_name: str
    local_time: str
    blood_pressure: str | None
    alert_level: str | None
    heart_rate_bpm: int | None
    sleep_hours: float | None
    doses: list[DoseOut]


class AlertOut(BaseModel):
    action: str
    title: str
    body: str
    recipients: list[str]
    created_at: datetime


class AlertsResponse(BaseModel):
    alerts: list[AlertOut]


class ScenarioResponse(BaseModel):
    scenario: str
    published: int


class BrainOut(BaseModel):
    provider: str
    model: str
    external: bool  # True when conversation data goes to a third party.
    fallback: bool


class ActivityEventOut(BaseModel):
    at: datetime
    kind: str
    text: str


class ActivityResponse(BaseModel):
    events: list[ActivityEventOut]


class ResetResponse(BaseModel):
    status: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    trace_id: str
    fields: list[dict[str, str]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
