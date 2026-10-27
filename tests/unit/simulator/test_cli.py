from builders import TODAY
from homewellness.demo import DEMO_ELDER_ID
from homewellness.simulator.__main__ import play


class FakePublisher:
    def __init__(self):
        self.sent = []

    def publish(self, topic, body):
        self.sent.append((topic, body))


def should_publish_every_message_in_order_when_a_scenario_is_played():
    publisher = FakePublisher()
    count = play("morning", DEMO_ELDER_ID, TODAY, publisher)
    assert count == 3 == len(publisher.sent)
    assert publisher.sent[0][0] == "homewellness/sim/clock"
