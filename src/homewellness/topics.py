"""MQTT topic names. The device, the simulator and the controller share them.

  homewellness/<elder_id>/vitals   blood pressure, heart rate, room temperature
  homewellness/<elder_id>/sleep    summary of the last night
  homewellness/sim/clock           demo only: move the clock of the worker
"""

PREFIX = "homewellness"
CLOCK_TOPIC = f"{PREFIX}/sim/clock"
_KINDS = frozenset({"vitals", "sleep"})


def _checked(elder_id: str) -> str:
    if not elder_id or any(char in elder_id for char in "/+#"):
        raise ValueError(f"elder id is not valid in a topic: {elder_id!r}")
    return elder_id


def vitals_topic(elder_id: str) -> str:
    return f"{PREFIX}/{_checked(elder_id)}/vitals"


def sleep_topic(elder_id: str) -> str:
    return f"{PREFIX}/{_checked(elder_id)}/sleep"


def parse_telemetry_topic(topic: str) -> tuple[str, str] | None:
    """Return (elder_id, kind), or None if this is not a telemetry topic."""
    parts = topic.split("/")
    if len(parts) != 3 or parts[0] != PREFIX or not parts[1] or parts[2] not in _KINDS:
        return None
    return parts[1], parts[2]


def subscriptions(demo_mode: bool) -> list[str]:
    topics = [f"{PREFIX}/+/vitals", f"{PREFIX}/+/sleep"]
    return [*topics, CLOCK_TOPIC] if demo_mode else topics
