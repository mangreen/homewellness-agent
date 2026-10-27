"""Rules that decide when the agent starts a conversation. Pure. No I/O.

The policy returns every trigger that applies now. It does not remember what it
sent. The controller removes duplicates with the `dedup_key`.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from homewellness.models.alert_policy import (
    DEFAULT_THRESHOLDS,
    AlertLevel,
    AlertThresholds,
    assess_blood_pressure,
)
from homewellness.models.medication import Dose, DoseState, MedicationSchedule, dose_states
from homewellness.models.vitals import (
    DEFAULT_VITALS_MAX_AGE,
    BloodPressure,
    SleepSummary,
    VitalsSnapshot,
)

# NOTE: Demo value. Below this many hours the agent asks about sleep.
POOR_SLEEP_HOURS = 5.0

_PROACTIVE_LEVELS = frozenset({AlertLevel.LOW, AlertLevel.HIGH, AlertLevel.CRITICAL})


class TriggerKind(StrEnum):
    ABNORMAL_VITALS = "abnormal_vitals"
    MEDICATION_DUE = "medication_due"
    POOR_SLEEP = "poor_sleep"


@dataclass(frozen=True, slots=True)
class ProactiveTrigger:
    kind: TriggerKind
    dedup_key: str
    dose: Dose | None = None
    alert_level: AlertLevel | None = None
    blood_pressure: BloodPressure | None = None
    sleep_hours: float | None = None


def evaluate_triggers(
    *,
    local_now: datetime,
    schedule: MedicationSchedule,
    taken_dose_ids: frozenset[str],
    vitals: VitalsSnapshot | None,
    sleep: SleepSummary | None,
    thresholds: AlertThresholds = DEFAULT_THRESHOLDS,
    vitals_max_age: timedelta = DEFAULT_VITALS_MAX_AGE,
) -> list[ProactiveTrigger]:
    """Return triggers in priority order: vitals, medication, sleep."""
    triggers: list[ProactiveTrigger] = []

    if vitals and vitals.blood_pressure and vitals.is_fresh(local_now, vitals_max_age):
        level = assess_blood_pressure(vitals.blood_pressure, thresholds)
        if level in _PROACTIVE_LEVELS:
            triggers.append(
                ProactiveTrigger(
                    TriggerKind.ABNORMAL_VITALS,
                    f"vitals:{vitals.measured_at.isoformat()}",
                    alert_level=level,
                    blood_pressure=vitals.blood_pressure,
                )
            )

    states = dose_states(schedule, taken_dose_ids, local_now)
    for dose in schedule.doses:
        if states[dose.dose_id] is DoseState.DUE:
            triggers.append(
                ProactiveTrigger(
                    TriggerKind.MEDICATION_DUE,
                    f"med:{local_now.date().isoformat()}:{dose.dose_id}",
                    dose=dose,
                )
            )

    if (
        sleep
        and sleep.woke_on == local_now.date()
        and sleep.hours_asleep < POOR_SLEEP_HOURS
    ):
        triggers.append(
            ProactiveTrigger(
                TriggerKind.POOR_SLEEP,
                f"sleep:{sleep.woke_on.isoformat()}",
                sleep_hours=sleep.hours_asleep,
            )
        )
    return triggers
