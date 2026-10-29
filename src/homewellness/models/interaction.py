"""Data objects shared by use cases and ports. No behavior and no I/O."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from homewellness.models.alert_policy import AlertLevel, EscalationAction
from homewellness.models.medication import Dose, DoseState
from homewellness.models.vitals import SleepSummary, VitalsSnapshot


class Recipient(StrEnum):
    FAMILY = "family"
    EMERGENCY_SERVICES = "emergency_services"


@dataclass(frozen=True, slots=True)
class Notification:
    elder_id: str
    action: EscalationAction
    title: str
    body: str
    recipients: tuple[Recipient, ...]
    created_at: datetime


class Role(StrEnum):
    ELDER = "elder"
    AGENT = "agent"


@dataclass(frozen=True, slots=True)
class ConversationTurn:
    role: Role
    text: str
    at: datetime


@dataclass(frozen=True, slots=True)
class DoseStatus:
    dose: Dose
    state: DoseState


@dataclass(frozen=True, slots=True)
class HealthContext:
    """What the agent may know about the elder right now."""

    elder_id: str
    display_name: str
    local_now: datetime
    vitals: VitalsSnapshot | None  # Fresh readings only.
    alert_level: AlertLevel | None
    sleep: SleepSummary | None  # Last night only.
    doses: tuple[DoseStatus, ...]


@dataclass(frozen=True, slots=True)
class AgentRequest:
    elder_id: str
    message: str
    context: HealthContext
    history: tuple[ConversationTurn, ...]
