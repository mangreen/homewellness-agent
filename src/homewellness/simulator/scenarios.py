"""Demo scenarios. Each scenario is a list of MQTT messages. The first message moves the clock.

Play them in order: morning, dizzy, crisis.
NOTE: The worker removes duplicate triggers. To replay a scenario, run `make demo-reset`.
"""

import json
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from homewellness.topics import CLOCK_TOPIC, sleep_topic, vitals_topic

SCENARIO_NAMES = ("morning", "dizzy", "crisis")
_TZ = ZoneInfo("Asia/Taipei")


@dataclass(frozen=True, slots=True)
class SimMessage:
    topic: str
    payload: dict

    def body(self) -> bytes:
        return json.dumps(self.payload).encode()


def _at(day: date, hour: int, minute: int) -> str:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=_TZ).isoformat()


def _clock(day: date, hour: int, minute: int) -> SimMessage:
    return SimMessage(CLOCK_TOPIC, {"now": _at(day, hour, minute)})


def _vitals(elder_id: str, day: date, hour: int, minute: int, systolic: int, diastolic: int,
            heart_rate: int) -> SimMessage:
    return SimMessage(vitals_topic(elder_id), {
        "measured_at": _at(day, hour, minute), "systolic": systolic, "diastolic": diastolic,
        "heart_rate_bpm": heart_rate,
    })


def build_scenario(name: str, elder_id: str, day: date) -> list[SimMessage]:
    if name == "morning":  # 08:05. Slept 4.5 hours. The morning dose is due.
        return [
            _clock(day, 8, 5),
            SimMessage(sleep_topic(elder_id), {"woke_on": day.isoformat(), "hours_asleep": 4.5}),
            _vitals(elder_id, day, 8, 4, 128, 82, 72),
        ]
    if name == "dizzy":  # 08:20. Blood pressure is elevated. The elder then says she is dizzy.
        return [_clock(day, 8, 20), _vitals(elder_id, day, 8, 19, 158, 98, 80)]
    if name == "crisis":  # 08:40. Blood pressure is in the critical range.
        return [_clock(day, 8, 40), _vitals(elder_id, day, 8, 39, 188, 121, 104)]
    raise ValueError(f"unknown scenario {name!r}. Use one of: {', '.join(SCENARIO_NAMES)}")
