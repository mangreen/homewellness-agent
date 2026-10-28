from datetime import timedelta
from types import SimpleNamespace

import pytest

from builders import ELDER_ID, make_vitals, taipei
from homewellness.controllers.agent_actions import AgentActionsController
from homewellness.controllers.escalation import EscalationController
from homewellness.controllers.medication import MedicationController
from homewellness.models.errors import DomainError
from homewellness.models.vitals import VitalsSnapshot


@pytest.fixture
def tools(env):
    calls = []
    medication = MedicationController(elders=env.elders, intakes=env.intakes, clock=env.clock)
    escalation = EscalationController(
        elders=env.elders, telemetry=env.telemetry, claims=env.claims, notifier=env.notifier,
        clock=env.clock,
    )
    actions = AgentActionsController(
        elders=env.elders, telemetry=env.telemetry, intakes=env.intakes, medication=medication,
        escalation=escalation, clock=env.clock, on_call=lambda name, elder: calls.append(name),
    )
    return SimpleNamespace(actions=actions, calls=calls)


def should_return_the_fresh_blood_pressure_and_its_level(tools, env):
    env.telemetry.save_vitals(make_vitals(taipei(8, 0), 158, 98))
    assert tools.actions.get_latest_vitals(ELDER_ID) == {
        "available": True, "blood_pressure": "158/98", "level": "elevated",
        "heart_rate_bpm": None, "measured_minutes_ago": 5}


def should_say_unavailable_when_there_is_no_reading(tools):
    assert tools.actions.get_latest_vitals(ELDER_ID) == {
        "available": False, "reason": "no_recent_reading"}


def should_say_unavailable_when_the_reading_is_stale(tools, env):
    env.telemetry.save_vitals(make_vitals(taipei(7, 0), 158, 98))
    assert tools.actions.get_latest_vitals(ELDER_ID)["available"] is False


def should_say_unavailable_when_the_reading_has_no_blood_pressure(tools, env):
    env.telemetry.save_vitals(VitalsSnapshot(ELDER_ID, taipei(8, 0), heart_rate_bpm=70))
    assert tools.actions.get_latest_vitals(ELDER_ID)["available"] is False


def should_list_the_medicine_and_the_state_of_each_dose(tools):
    assert tools.actions.get_medication_status(ELDER_ID) == {
        "medication": "blood pressure medicine",
        "doses": [{"dose_id": "am", "label": "morning", "time": "08:00", "state": "due"},
                  {"dose_id": "pm", "label": "evening", "time": "20:00", "state": "upcoming"}]}


def should_log_the_intake_and_report_the_status(tools):
    first = tools.actions.log_medication_intake(ELDER_ID)
    second = tools.actions.log_medication_intake(ELDER_ID)
    assert first == {"status": "recorded", "dose": "morning"}
    assert second["status"] == "already_taken"


def should_report_no_dose_due_when_it_is_too_early(tools, env):
    env.clock.set(taipei(6, 0))
    assert tools.actions.log_medication_intake(ELDER_ID) == {"status": "no_dose_due", "dose": None}


def should_let_the_policy_send_an_alert_when_the_agent_asks_for_it(tools, env):
    env.telemetry.save_vitals(make_vitals(taipei(8, 4), 188, 121))
    result = tools.actions.escalate_emergency(ELDER_ID, ["chest_pain"])
    assert (result["status"], result["action"]) == ("sent", "call_emergency")
    assert len(env.notifier.sent) == 1


def should_refuse_the_request_when_the_policy_finds_no_reason(tools, env):
    env.telemetry.save_vitals(make_vitals(taipei(8, 4), 120, 80))
    result = tools.actions.escalate_emergency(ELDER_ID, ["dizziness"])
    assert (result["status"], result["action"]) == ("suppressed_by_policy", "none")
    assert env.notifier.sent == []


def should_send_the_alert_once_when_the_agent_repeats_the_request_in_ten_minutes(tools, env):
    env.telemetry.save_vitals(make_vitals(taipei(8, 4), 188, 121))
    tools.actions.escalate_emergency(ELDER_ID, ["chest_pain"])
    second = tools.actions.escalate_emergency(ELDER_ID, ["chest_pain"])
    assert second["status"] == "duplicate" and len(env.notifier.sent) == 1


def should_send_a_new_alert_when_the_situation_lasts_beyond_ten_minutes(tools, env):
    env.telemetry.save_vitals(make_vitals(taipei(8, 4), 188, 121))
    tools.actions.escalate_emergency(ELDER_ID, ["chest_pain"])
    env.clock.set(env.clock.now() + timedelta(minutes=11))
    assert tools.actions.escalate_emergency(ELDER_ID, ["chest_pain"])["status"] == "sent"
    assert len(env.notifier.sent) == 2


def should_raise_a_domain_error_when_the_symptom_is_unknown(tools):
    with pytest.raises(DomainError):
        tools.actions.escalate_emergency(ELDER_ID, ["toothache"])


def should_tell_the_observer_about_each_call_in_order(tools):
    tools.actions.get_latest_vitals(ELDER_ID)
    tools.actions.get_medication_status(ELDER_ID)
    assert tools.calls == ["get_latest_vitals", "get_medication_status"]


def should_work_without_an_observer_when_none_is_given(env):
    medication = MedicationController(elders=env.elders, intakes=env.intakes, clock=env.clock)
    escalation = EscalationController(
        elders=env.elders, telemetry=env.telemetry, claims=env.claims, notifier=env.notifier,
        clock=env.clock,
    )
    actions = AgentActionsController(
        elders=env.elders, telemetry=env.telemetry, intakes=env.intakes, medication=medication,
        escalation=escalation, clock=env.clock,
    )
    assert actions.get_latest_vitals(ELDER_ID)["available"] is False
