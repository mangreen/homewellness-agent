"""Controller: turn a device message into a telemetry ingest.

A bad message is dropped and logged. It never stops the worker.
NOTE: Logs hold the topic and the reason only. They never hold the payload (personal data).
"""

import logging
from collections.abc import Callable
from datetime import date

from pydantic import AwareDatetime, BaseModel, ConfigDict, ValidationError, model_validator

from homewellness.controllers.telemetry import TelemetryController
from homewellness.interfaces import SettableClock
from homewellness.models.errors import DomainError
from homewellness.models.trigger_policy import ProactiveTrigger
from homewellness.models.vitals import BloodPressure, SleepSummary, VitalsSnapshot
from homewellness.observability import bind_context, new_trace_id
from homewellness.topics import CLOCK_TOPIC, parse_telemetry_topic

logger = logging.getLogger("homewellness.mqtt")

TriggersCallback = Callable[[str, list[ProactiveTrigger]], None]


class _Message(BaseModel):
    model_config = ConfigDict(extra="forbid")  # Reject unknown fields.


class VitalsMessage(_Message):
    measured_at: AwareDatetime
    systolic: int | None = None
    diastolic: int | None = None
    heart_rate_bpm: int | None = None
    room_temperature_c: float | None = None

    @model_validator(mode="after")
    def _blood_pressure_needs_both_values(self) -> "VitalsMessage":
        if (self.systolic is None) != (self.diastolic is None):
            raise ValueError("systolic and diastolic must come together")
        return self


class SleepMessage(_Message):
    woke_on: date
    hours_asleep: float


class ClockMessage(_Message):
    now: AwareDatetime


def _describe_reading(reading: VitalsSnapshot | SleepSummary) -> str:
    if isinstance(reading, SleepSummary):
        return f"裝置回報：睡眠 {reading.hours_asleep:g} 小時"
    parts = []
    if reading.blood_pressure:
        parts.append(f"血壓 {reading.blood_pressure}")
    if reading.heart_rate_bpm is not None:
        parts.append(f"心率 {reading.heart_rate_bpm}")
    return "裝置回報：" + "、".join(parts)


class MqttController:
    def __init__(
        self,
        *,
        telemetry: TelemetryController,
        on_triggers: TriggersCallback,
        on_event: Callable[[str, str], None] | None = None,
        clock_control: SettableClock | None = None,
    ) -> None:
        self._telemetry = telemetry
        self._on_triggers = on_triggers
        self._on_event = on_event  # (kind, text) for the demo timeline
        self._clock_control = clock_control  # Set only in demo mode.

    def handle_message(self, topic: str, payload: bytes) -> list[ProactiveTrigger]:
        parsed = parse_telemetry_topic(topic)
        # A new trace-id starts at this entry point. All later logs share it.
        with bind_context(trace_id=new_trace_id(), user_id=parsed[0] if parsed else "-"):
            try:
                return self._dispatch(topic, parsed, payload)
            except (ValidationError, DomainError) as error:
                logger.warning(
                    "message dropped",
                    extra={"event": "message_dropped", "topic": topic,
                           "reason": type(error).__name__},
                )
                return []

    def _dispatch(
        self, topic: str, parsed: tuple[str, str] | None, payload: bytes
    ) -> list[ProactiveTrigger]:
        if topic == CLOCK_TOPIC:
            return self._handle_clock(payload)
        if parsed is None:
            raise DomainError("unknown topic")
        elder_id, kind = parsed

        if kind == "vitals":
            vitals = VitalsMessage.model_validate_json(payload)
            blood_pressure = None
            if vitals.systolic is not None and vitals.diastolic is not None:
                blood_pressure = BloodPressure(vitals.systolic, vitals.diastolic)
            reading = VitalsSnapshot(
                elder_id, vitals.measured_at, blood_pressure, vitals.heart_rate_bpm,
                vitals.room_temperature_c,
            )
        else:
            sleep = SleepMessage.model_validate_json(payload)
            reading = SleepSummary(elder_id, sleep.woke_on, sleep.hours_asleep)

        triggers = self._telemetry.ingest(elder_id, reading)
        logger.info("telemetry ingested", extra={"event": "telemetry_ingested", "kind": kind})
        self._emit("device", _describe_reading(reading))
        for trigger in triggers:
            logger.info(
                "proactive trigger",
                extra={"event": "proactive_trigger", "trigger_kind": trigger.kind.value,
                       "dedup_key": trigger.dedup_key},
            )
        if triggers:
            self._on_triggers(elder_id, triggers)
        return triggers

    def _emit(self, kind: str, text: str) -> None:
        if self._on_event is not None:
            self._on_event(kind, text)

    def _handle_clock(self, payload: bytes) -> list[ProactiveTrigger]:
        message = ClockMessage.model_validate_json(payload)
        if self._clock_control is None:
            logger.info("clock message ignored", extra={"event": "clock_ignored"})
        else:
            self._clock_control.set(message.now)
            self._emit("clock", f"（Demo）時間設為 {message.now:%H:%M}")
            logger.info("clock set", extra={"event": "clock_set", "now": message.now.isoformat()})
        return []
