import asyncio

import httpx
import pytest

from tests_support import ELDER, key

pytestmark = pytest.mark.concurrency


def burst(app, requests):
    async def run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await asyncio.gather(*[client.post(*r[0], **r[1]) for r in requests])

    return asyncio.run(run())


def should_accept_one_request_and_reject_nine_when_ten_requests_share_a_key(app, container):
    request = ((f"/elders/{ELDER}/messages",),
               {"json": {"text": "你好"}, "headers": {"Idempotency-Key": "same-key-0001"}})
    codes = sorted(r.status_code for r in burst(app, [request] * 10))
    assert codes == [200] + [409] * 9
    assert len(container.chat.history(ELDER, 10)) == 2


def should_send_one_alert_when_ten_requests_report_chest_pain_at_once(app, container):
    for message in container_messages(container):
        container.mqtt.handle_message(*message)
    requests = [((f"/elders/{ELDER}/messages",),
                 {"json": {"text": "我胸口有點悶"}, "headers": {"Idempotency-Key": key()}})
                for _ in range(10)]
    assert all(r.status_code == 200 for r in burst(app, requests))
    assert len(container.notifier.list_sent()) == 1


def container_messages(container):
    from datetime import date

    from homewellness.simulator.scenarios import build_scenario

    return [(m.topic, m.body()) for m in build_scenario("crisis", ELDER, date(2026, 10, 27))]
