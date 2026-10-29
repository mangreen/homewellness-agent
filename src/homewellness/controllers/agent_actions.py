"""Controller: the actions that the agent can ask for (its tools).

Each action returns a plain dict. The agent never gets a store or a controller.
The safety policy has the last word on alerts. The agent can only ask.
"""

import logging
from collections.abc import Callable

from homewellness.controllers.escalation import EscalationController
from homewellness.controllers.health_context import current_vitals
from homewellness.controllers.medication import MedicationController
from homewellness.interfaces import Clock, ElderStore, IntakeStore, TelemetryStore
from homewellness.models.errors import DomainError
from homewellness.models.symptoms import Symptom

logger = logging.getLogger("homewellness.agent")

# An alert request from the agent is repeated for this long without a second alert.
_ESCALATION_WINDOW_SECONDS = 600


class AgentActionsController:
    def __init__(
        self,
        *,
        elders: ElderStore,
        telemetry: TelemetryStore,
        intakes: IntakeStore,
        medication: MedicationController,
        escalation: EscalationController,
        clock: Clock,
        on_call: Callable[[str, str], None] | None = None,
    ) -> None:
        self._elders = elders
        self._telemetry = telemetry
        self._medication = medication
        self._escalation = escalation
        self._clock = clock
        self._on_call = on_call

    def _called(self, tool: str, elder_id: str) -> None:
        logger.info("tool called", extra={"event": "tool_called", "tool": tool})
        if self._on_call is not None:
            self._on_call(tool, elder_id)

    def get_latest_vitals(self, elder_id: str) -> dict:
        self._called("get_latest_vitals", elder_id)
        now = self._clock.now()
        vitals, level = current_vitals(self._telemetry, elder_id, now)
        if vitals is None or vitals.blood_pressure is None or level is None:
            return {"available": False, "reason": "no_recent_reading"}
        minutes = int((now - vitals.measured_at).total_seconds() // 60)
        return {
            "available": True,
            "blood_pressure": str(vitals.blood_pressure),
            "level": level.value,
            "heart_rate_bpm": vitals.heart_rate_bpm,
            "measured_minutes_ago": max(minutes, 0),
        }

    def get_medication_status(self, elder_id: str) -> dict:
        self._called("get_medication_status", elder_id)
        profile = self._elders.get(elder_id)
        return {
            "medication": profile.medication_schedule.medication_name,
            "doses": [
                {"dose_id": s.dose.dose_id, "label": s.dose.label,
                 "time": f"{s.dose.time_of_day:%H:%M}", "state": s.state.value}
                for s in self._medication.status(elder_id)
            ],
        }

    def log_medication_intake(self, elder_id: str) -> dict:
        self._called("log_medication_intake", elder_id)
        result = self._medication.record_intake(elder_id)
        return {"status": result.status.value, "dose": result.dose.label if result.dose else None}

    def escalate_emergency(self, elder_id: str, symptoms: list[str]) -> dict:
        self._called("escalate_emergency", elder_id)
        try:
            parsed = frozenset(Symptom(name) for name in symptoms)
        except ValueError as error:
            raise DomainError("unknown symptom") from error
        bucket = int(self._clock.now().timestamp() // _ESCALATION_WINDOW_SECONDS)
        key = f"agent:{','.join(sorted(s.value for s in parsed))}:{bucket}"
        outcome = self._escalation.escalate(elder_id, parsed, key)
        return {
            "status": outcome.status.value,
            "action": outcome.decision.action.value,
            "reason": outcome.decision.reason,
        }
