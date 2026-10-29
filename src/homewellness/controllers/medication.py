"""Controller: the elder says that they took their medicine."""

from homewellness.controllers.health_context import taken_dose_ids
from homewellness.interfaces import Clock, ElderStore, IntakeStore
from homewellness.models.medication import (
    IntakeResolution,
    IntakeStatus,
    MedicationIntake,
    resolve_intake,
)


class MedicationController:
    def __init__(
        self, *, elders: ElderStore, intakes: IntakeStore, clock: Clock
    ) -> None:
        self._elders = elders
        self._intakes = intakes
        self._clock = clock

    def record_intake(self, elder_id: str) -> IntakeResolution:
        profile = self._elders.get(elder_id)
        now = self._clock.now()
        local_now = profile.local_now(now)
        taken = taken_dose_ids(self._intakes, profile, local_now)
        resolution = resolve_intake(profile.medication_schedule, taken, local_now)
        if resolution.status is not IntakeStatus.RECORDED:
            return resolution
        intake = MedicationIntake(elder_id, resolution.dose.dose_id, local_now.date(), now)
        # NOTE: A parallel request can win the race. The atomic add tells us.
        if not self._intakes.add(intake):
            return IntakeResolution(IntakeStatus.ALREADY_TAKEN, resolution.dose)
        return resolution
