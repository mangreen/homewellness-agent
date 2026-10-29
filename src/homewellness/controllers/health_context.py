"""Build the HealthContext that the agent receives."""

from datetime import datetime

from homewellness.interfaces import IntakeStore, TelemetryStore
from homewellness.models.alert_policy import assess_blood_pressure
from homewellness.models.elder import ElderProfile
from homewellness.models.interaction import DoseStatus, HealthContext
from homewellness.models.medication import dose_states


def taken_dose_ids(
    intakes: IntakeStore, profile: ElderProfile, local_now: datetime
) -> frozenset[str]:
    stored = intakes.list_for_date(profile.elder_id, local_now.date())
    return frozenset(intake.dose_id for intake in stored)


def build_health_context(
    *,
    profile: ElderProfile,
    telemetry: TelemetryStore,
    intakes: IntakeStore,
    now: datetime,
) -> HealthContext:
    local_now = profile.local_now(now)
    vitals = telemetry.latest_vitals(profile.elder_id)
    if vitals is not None and not vitals.is_fresh(now):
        vitals = None
    level = (
        assess_blood_pressure(vitals.blood_pressure) if vitals and vitals.blood_pressure else None
    )
    sleep = telemetry.latest_sleep(profile.elder_id)
    if sleep is not None and sleep.woke_on != local_now.date():
        sleep = None
    states = dose_states(
        profile.medication_schedule, taken_dose_ids(intakes, profile, local_now), local_now
    )
    doses = tuple(DoseStatus(d, states[d.dose_id]) for d in profile.medication_schedule.doses)
    return HealthContext(
        profile.elder_id, profile.display_name, local_now, vitals, level, sleep, doses
    )
