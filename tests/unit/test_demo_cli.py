from builders import taipei
from homewellness.demo_cli import run_demo
from homewellness.services.clock import FixedClock


def play():
    lines = []
    run_demo(lines.append, clock=FixedClock(taipei(15, 0)))
    return "\n".join(lines)


def should_show_the_four_scenes_when_the_demo_runs():
    text = play()
    for scene in ("場景 A", "場景 B", "場景 C", "場景 D"):
        assert scene in text


def should_show_the_tool_calls_and_the_greeting_when_the_demo_runs():
    text = play()
    for expected in ("log_medication_intake", "get_latest_vitals", "escalate_emergency", "早安"):
        assert expected in text


def should_send_exactly_two_alerts_and_mention_119_when_the_demo_runs():
    text = play()
    assert text.count("🚨 警報") == 2 and "119" in text


def should_call_the_pause_hook_between_scenes_when_step_mode_is_used():
    pauses = []
    run_demo(lambda line: None, pause=lambda: pauses.append(1), clock=FixedClock(taipei(15, 0)))
    assert len(pauses) == 4
