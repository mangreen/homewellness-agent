"""Play a demo scenario: `python -m homewellness.simulator morning`."""

import argparse
import os
from datetime import date, datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from homewellness.demo import DEMO_ELDER_ID
from homewellness.services.mqtt import MqttPublisher
from homewellness.simulator.scenarios import SCENARIO_NAMES, build_scenario


class Publisher(Protocol):
    def publish(self, topic: str, body: bytes) -> None: ...


def play(name: str, elder_id: str, day: date, publisher: Publisher) -> int:
    messages = build_scenario(name, elder_id, day)
    for message in messages:
        publisher.publish(message.topic, message.body())
        print(f"published {message.topic}")
    return len(messages)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Play a demo scenario over MQTT.")
    parser.add_argument("scenario", choices=SCENARIO_NAMES)
    parser.add_argument("--elder", default=DEMO_ELDER_ID)
    parser.add_argument("--host", default=os.environ.get("MQTT_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("MQTT_PORT", "1883")))
    parser.add_argument("--day", type=date.fromisoformat,
                        default=datetime.now(ZoneInfo("Asia/Taipei")).date())
    args = parser.parse_args(argv)
    publisher = MqttPublisher(args.host, args.port)
    try:
        play(args.scenario, args.elder, args.day, publisher)
    finally:
        publisher.close()


if __name__ == "__main__":
    main()
