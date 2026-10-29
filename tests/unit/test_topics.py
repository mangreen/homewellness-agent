import pytest

from homewellness.topics import CLOCK_TOPIC, parse_telemetry_topic, sleep_topic, vitals_topic


def should_build_topics_when_an_elder_id_is_given():
    assert vitals_topic("e1") == "homewellness/e1/vitals"
    assert sleep_topic("e1") == "homewellness/e1/sleep"
    assert CLOCK_TOPIC == "homewellness/sim/clock"


def should_parse_the_elder_and_kind_when_the_topic_is_a_telemetry_topic():
    assert parse_telemetry_topic(vitals_topic("e1")) == ("e1", "vitals")
    assert parse_telemetry_topic(sleep_topic("e1")) == ("e1", "sleep")


@pytest.mark.parametrize(
    "topic",
    ["other/e1/vitals", "homewellness/e1/unknown", "homewellness/e1", "homewellness/e1/vitals/x",
     CLOCK_TOPIC],
)
def should_return_none_when_the_topic_is_not_a_telemetry_topic(topic):
    assert parse_telemetry_topic(topic) is None


@pytest.mark.parametrize("bad_id", ["", "a/b", "a+b", "a#b"])
def should_reject_an_elder_id_when_it_breaks_the_topic_format(bad_id):
    with pytest.raises(ValueError):
        vitals_topic(bad_id)
