"""Controller: alert family or emergency contacts. The policy decides, not the LLM."""

from dataclasses import dataclass
from enum import StrEnum

from homewellness.interfaces import (
    ClaimStore,
    Clock,
    ElderStore,
    Notifier,
    TelemetryStore,
)
from homewellness.models.alert_policy import (
    AlertLevel,
    EscalationAction,
    EscalationDecision,
    assess_blood_pressure,
    decide_escalation,
)
from homewellness.models.symptoms import Symptom
from homewellness.views.notifications import compose_notification


class EscalationStatus(StrEnum):
    SENT = "sent"
    SUPPRESSED_BY_POLICY = "suppressed_by_policy"
    DUPLICATE = "duplicate"


@dataclass(frozen=True, slots=True)
class EscalationOutcome:
    status: EscalationStatus
    decision: EscalationDecision


class EscalationController:
    def __init__(
        self,
        *,
        elders: ElderStore,
        telemetry: TelemetryStore,
        claims: ClaimStore,
        notifier: Notifier,
        clock: Clock,
    ) -> None:
        self._elders = elders
        self._telemetry = telemetry
        self._claims = claims
        self._notifier = notifier
        self._clock = clock

    def escalate(
        self, elder_id: str, symptoms: frozenset[Symptom], idempotency_key: str
    ) -> EscalationOutcome:
        profile = self._elders.get(elder_id)
        now = self._clock.now()

        vitals = self._telemetry.latest_vitals(elder_id)
        blood_pressure = (
            vitals.blood_pressure if vitals and vitals.is_fresh(now) else None
        )
        level: AlertLevel | None = (
            assess_blood_pressure(blood_pressure) if blood_pressure else None
        )
        decision = decide_escalation(level, symptoms)
        if decision.action is EscalationAction.NONE:
            return EscalationOutcome(EscalationStatus.SUPPRESSED_BY_POLICY, decision)

        claim_key = f"escalation:{elder_id}:{idempotency_key}"
        if not self._claims.try_claim(claim_key):
            return EscalationOutcome(EscalationStatus.DUPLICATE, decision)
        try:
            self._notifier.send(
                compose_notification(
                    profile=profile, blood_pressure=blood_pressure, symptoms=symptoms,
                    decision=decision, created_at=now,
                )
            )
        except Exception:
            # NOTE: A lost alert is unsafe. Free the key so that a retry can send it.
            self._claims.release(claim_key)
            raise
        return EscalationOutcome(EscalationStatus.SENT, decision)
