from builders import taipei
from homewellness.services.activity import ActivityLog
from homewellness.services.clock import FixedClock


def should_stamp_each_event_with_the_clock_time():
    log = ActivityLog(FixedClock(taipei(8, 5)))
    log.add("tool", "Agent 呼叫工具：get_latest_vitals")
    event = log.recent(10)[0]
    assert (event.at, event.kind, event.text) == (
        taipei(8, 5), "tool", "Agent 呼叫工具：get_latest_vitals")


def should_keep_only_the_newest_events_when_the_limit_is_reached():
    log = ActivityLog(FixedClock(taipei(8, 5)), max_events=3)
    for index in range(5):
        log.add("device", f"e{index}")
    assert [e.text for e in log.recent(10)] == ["e2", "e3", "e4"]


def should_return_the_newest_events_oldest_first_when_a_limit_is_given():
    log = ActivityLog(FixedClock(taipei(8, 5)))
    for index in range(5):
        log.add("device", f"e{index}")
    assert [e.text for e in log.recent(2)] == ["e3", "e4"]


def should_forget_all_events_when_it_is_cleared():
    log = ActivityLog(FixedClock(taipei(8, 5)))
    log.add("device", "x")
    log.clear()
    assert log.recent(10) == []
