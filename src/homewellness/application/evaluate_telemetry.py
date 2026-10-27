"""Use case: store a device reading (if any) and find new proactive triggers."""

from homewellness.application.health_context import taken_dose_ids
from homewellness.application.ports import (
    ClaimStore,
    Clock,
    ElderRepository,
    IntakeRepository,
    TelemetryRepository,
)
from homewellness.domain.errors import DomainError
from homewellness.domain.trigger_policy import ProactiveTrigger, evaluate_triggers
from homewellness.domain.vitals import SleepSummary, VitalsSnapshot

Reading = VitalsSnapshot | SleepSummary


class EvaluateTelemetry:
    def __init__(
        self,
        *,
        elders: ElderRepository,
        telemetry: TelemetryRepository,
        intakes: IntakeRepository,
        claims: ClaimStore,
        clock: Clock,
    ) -> None:
        self._elders = elders
        self._telemetry = telemetry
        self._intakes = intakes
        self._claims = claims
        self._clock = clock

    def execute(self, elder_id: str, reading: Reading | None = None) -> list[ProactiveTrigger]:
        """Run with a reading (device event) or without one (scheduled tick)."""
        profile = self._elders.get(elder_id)
        if reading is not None and reading.elder_id != elder_id:
            raise DomainError("reading belongs to another elder")
        if isinstance(reading, VitalsSnapshot):
            self._telemetry.save_vitals(reading)
        elif isinstance(reading, SleepSummary):
            self._telemetry.save_sleep(reading)

        local_now = profile.local_now(self._clock.now())
        candidates = evaluate_triggers(
            local_now=local_now,
            schedule=profile.medication_schedule,
            taken_dose_ids=taken_dose_ids(self._intakes, profile, local_now),
            vitals=self._telemetry.latest_vitals(elder_id),
            sleep=self._telemetry.latest_sleep(elder_id),
        )
        # The atomic claim makes sure that each trigger is returned only once.
        return [
            t for t in candidates
            if self._claims.try_claim(f"trigger:{elder_id}:{t.dedup_key}")
        ]
