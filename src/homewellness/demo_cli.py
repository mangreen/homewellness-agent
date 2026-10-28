"""Run the whole demo story in the terminal: `python -m homewellness.demo_cli [--step]`.

It needs no Docker service and no network. It uses the same controllers as the API.
"""

import argparse
from collections.abc import Callable
from datetime import datetime
from zoneinfo import ZoneInfo

from homewellness.bootstrap import build_container
from homewellness.demo import DEMO_ELDER_ID
from homewellness.interfaces import Clock
from homewellness.settings import Settings
from homewellness.simulator.scenarios import build_scenario


def run_demo(
    say: Callable[[str], None],
    *,
    pause: Callable[[], None] = lambda: None,
    clock: Clock | None = None,
) -> None:
    container = build_container(
        Settings(store_backend="memory", demo_mode=True), clock=clock,
        on_tool_call=lambda tool, elder_id: say(f"   🔧 工具呼叫：{tool}"),
    )
    today = datetime.now(ZoneInfo("Asia/Taipei")).date()
    shown = {"turns": 0, "alerts": 0}

    def device(text: str, scenario: str) -> None:
        say(f"📡 裝置：{text}")
        for message in build_scenario(scenario, DEMO_ELDER_ID, today):
            container.mqtt.handle_message(message.topic, message.body())
        show_new()

    def show_new() -> None:
        turns = container.chat.history(DEMO_ELDER_ID, 50)
        for turn in turns[shown["turns"]:]:
            if turn.role.value == "agent":
                say(f"🤖 Agent：{turn.text}")
        shown["turns"] = len(turns)
        alerts = container.notifier.list_sent()
        for alert in alerts[shown["alerts"]:]:
            say(f"🚨 警報 [{alert.action.value}] → {', '.join(r.value for r in alert.recipients)}")
            say(f"   {alert.body}")
        shown["alerts"] = len(alerts)

    def elder(text: str) -> None:
        say(f"👵 王奶奶：{text}")
        say(f"🤖 Agent：{container.chat.reply(DEMO_ELDER_ID, text)}")
        shown["turns"] = len(container.chat.history(DEMO_ELDER_ID, 50))
        show_new()

    say("━━ 場景 A｜早上主動關懷（IoT 數據 → Agent 主動開口）")
    device("08:05 睡眠 4.5 小時、血壓 128/82", "morning")
    elder("吃了")
    pause()
    say("━━ 場景 B｜長者說頭暈（Tool Calling + 通知家人）")
    device("08:19 血壓 158/98", "dizzy")
    elder("我今天頭有點暈")
    pause()
    say("━━ 場景 C｜血壓危急（程式規則決定通報）")
    device("08:39 血壓 188/121", "crisis")
    elder("我胸口有點悶")
    pause()
    say("━━ 場景 D｜冪等與 Memory（重複請求不重複通報）")
    elder("我胸口有點悶")
    elder("我今天吃藥了嗎？")
    pause()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the demo story in the terminal.")
    parser.add_argument("--step", action="store_true", help="wait for Enter after each scene")
    args = parser.parse_args()
    run_demo(print, pause=(lambda: input("\n（按 Enter 繼續）\n")) if args.step else (lambda: None))


if __name__ == "__main__":
    main()
