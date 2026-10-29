"""The whole demo story through the HTTP API. No network and no Docker."""

from tests_support import ELDER, key


def should_play_the_whole_demo_story_through_the_api(client):
    def start(name):
        response = client.post(f"/sim/scenarios/{name}", headers={"Idempotency-Key": key()})
        assert response.status_code == 200

    def say(text):
        response = client.post(f"/elders/{ELDER}/messages", json={"text": text},
                               headers={"Idempotency-Key": key()})
        assert response.status_code == 200
        return response.json()["reply"]

    def turns():
        return client.get(f"/elders/{ELDER}/conversation?limit=50").json()["turns"]

    def alerts():
        return client.get("/alerts").json()["alerts"]

    # Scene A: the device sends data. The agent starts the conversation.
    start("morning")
    assert len(turns()) == 1 and turns()[0]["role"] == "agent"
    assert "早安" in turns()[0]["text"] and "降血壓藥" in turns()[0]["text"]
    assert "記下" in say("吃了")
    status = client.get(f"/elders/{ELDER}/status").json()
    assert {d["dose_id"]: d["state"] for d in status["doses"]}["am"] == "taken"

    # Scene B: the elder says she is dizzy. The agent reads the vitals and informs the family.
    start("dizzy")
    assert len(turns()) == 3  # No new greeting: nothing needs attention yet.
    reply = say("我今天頭有點暈")
    assert "158/98" in reply and "小美" in reply
    assert [a["action"] for a in alerts()] == ["notify_family"]

    # Scene C: critical reading. The agent asks, the elder reports chest tightness.
    start("crisis")
    assert "188/121" in turns()[-1]["text"] and turns()[-1]["role"] == "agent"
    assert "119" in say("我胸口有點悶")
    assert [a["action"] for a in alerts()] == ["notify_family", "call_emergency"]
    assert "emergency_services" in alerts()[1]["recipients"]

    # Scene D: a repeat sends no second alert. The agent remembers the medicine.
    say("我胸口有點悶")
    assert len(alerts()) == 2
    assert "已經吃過" in say("我今天吃藥了嗎？")
