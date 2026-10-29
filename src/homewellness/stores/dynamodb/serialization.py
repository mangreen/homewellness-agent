"""Convert domain objects to JSON text and back. DynamoDB stores the text in `data`.

NOTE: JSON text avoids the float restriction of the DynamoDB SDK and stays readable in a demo.
"""

import json
from datetime import UTC, date, datetime

from homewellness.models.interaction import ConversationTurn, Role
from homewellness.models.medication import MedicationIntake
from homewellness.models.vitals import BloodPressure, SleepSummary, VitalsSnapshot


def time_key(moment: datetime) -> str:
    """Fixed-width UTC text. Text order equals time order, so it works as a sort key."""
    return moment.astimezone(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def encode_vitals(v: VitalsSnapshot) -> str:
    bp = v.blood_pressure
    return json.dumps({
        "elder_id": v.elder_id, "measured_at": v.measured_at.isoformat(),
        "systolic": bp.systolic if bp else None, "diastolic": bp.diastolic if bp else None,
        "heart_rate_bpm": v.heart_rate_bpm, "room_temperature_c": v.room_temperature_c,
    })


def decode_vitals(text: str) -> VitalsSnapshot:
    d = json.loads(text)
    bp = BloodPressure(d["systolic"], d["diastolic"]) if d["systolic"] is not None else None
    return VitalsSnapshot(
        d["elder_id"], datetime.fromisoformat(d["measured_at"]), bp,
        d["heart_rate_bpm"], d["room_temperature_c"],
    )


def encode_sleep(s: SleepSummary) -> str:
    return json.dumps(
        {"elder_id": s.elder_id, "woke_on": s.woke_on.isoformat(), "hours_asleep": s.hours_asleep}
    )


def decode_sleep(text: str) -> SleepSummary:
    d = json.loads(text)
    return SleepSummary(d["elder_id"], date.fromisoformat(d["woke_on"]), d["hours_asleep"])


def encode_intake(i: MedicationIntake) -> str:
    return json.dumps({
        "elder_id": i.elder_id, "dose_id": i.dose_id,
        "local_date": i.local_date.isoformat(), "taken_at": i.taken_at.isoformat(),
    })


def decode_intake(text: str) -> MedicationIntake:
    d = json.loads(text)
    return MedicationIntake(
        d["elder_id"], d["dose_id"], date.fromisoformat(d["local_date"]),
        datetime.fromisoformat(d["taken_at"]),
    )


def encode_turn(t: ConversationTurn) -> str:
    return json.dumps({"role": t.role.value, "text": t.text, "at": t.at.isoformat()})


def decode_turn(text: str) -> ConversationTurn:
    d = json.loads(text)
    return ConversationTurn(Role(d["role"]), d["text"], datetime.fromisoformat(d["at"]))
