"""Build the HealthContext that the agent and the status endpoint use."""

from datetime import datetime

from homewellness.interfaces import IntakeStore, TelemetryStore
from homewellness.models.alert_policy import AlertLevel, assess_blood_pressure
from homewellness.models.elder import ElderProfile
from homewellness.models.interaction import DoseStatus, HealthContext
from homewellness.models.medication import dose_states
from homewellness.models.vitals import VitalsSnapshot


def taken_dose_ids(
    intakes: IntakeStore, profile: ElderProfile, local_now: datetime
) -> frozenset[str]:
    stored = intakes.list_for_date(profile.elder_id, local_now.date())
    return frozenset(intake.dose_id for intake in stored)


def current_vitals(
    telemetry: TelemetryStore, elder_id: str, now: datetime
) -> tuple[VitalsSnapshot | None, AlertLevel | None]:
    """Return the newest reading if it is fresh, with its blood pressure level."""
    vitals = telemetry.latest_vitals(elder_id)
    if vitals is None or not vitals.is_fresh(now):
        return None, None
    level = assess_blood_pressure(vitals.blood_pressure) if vitals.blood_pressure else None
    return vitals, level


def build_health_context(
    *,
    profile: ElderProfile,
    telemetry: TelemetryStore,
    intakes: IntakeStore,
    now: datetime,
) -> HealthContext:
    local_now = profile.local_now(now)
    vitals, level = current_vitals(telemetry, profile.elder_id, now)
    sleep = telemetry.latest_sleep(profile.elder_id)
    if sleep is not None and sleep.woke_on != local_now.date():
        sleep = None
    states = dose_states(
        profile.medication_schedule, taken_dose_ids(intakes, profile, local_now), local_now
    )
    doses = tuple(DoseStatus(d, states[d.dose_id]) for d in profile.medication_schedule.doses)
    return HealthContext(
        profile.elder_id, profile.display_name, local_now, vitals, level, sleep, doses,
        profile.medication_schedule.medication_name, profile.family_contact_name,
    )
