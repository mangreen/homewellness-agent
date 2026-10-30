"""Demo page: chat, device simulator and live status. It uses the HTTP API only."""

import os

import streamlit as st

from api_client import ApiError, ApiUnavailable, build_client
from view_models import (
    QUICK_REPLIES,
    SCENARIOS,
    activity_rows,
    alert_row,
    brain_label,
    dose_rows,
    external_warning,
    level_badge,
    local_time,
)

REFRESH_SECONDS = 2

st.set_page_config(page_title="HomeWellness Companion", page_icon="🏠", layout="wide")

if "client" not in st.session_state:
    st.session_state.client = build_client()
client = st.session_state.client


def guarded(call, *args):
    """Run an API call. Show a short message with the trace-id, never a stack trace."""
    try:
        return call(*args)
    except ApiError as error:
        st.error(f"{error.message}（代碼 `{error.code}`，trace-id `{error.trace_id}`）")
    except ApiUnavailable:
        st.error("連不上 API。請確認 `make up` 已完成，而且 app 顯示 healthy。")
    return None


@st.fragment(run_every=REFRESH_SECONDS)
def conversation_view(api):
    turns = guarded(api.conversation, 30)
    if turns is None:
        return
    if not turns:
        st.info("還沒有對話。按中間的「場景 A」讓 Agent 主動開口，或直接跟 Agent 說話。")
    for turn in turns:
        elder = turn["role"] == "elder"
        with st.chat_message("user" if elder else "assistant", avatar="👵" if elder else "🤖"):
            st.markdown(turn["text"])
            st.caption(local_time(turn["at"]))


@st.fragment(run_every=REFRESH_SECONDS)
def status_view(api):
    status = guarded(api.status)
    if status is None:
        return
    st.subheader("📊 即時狀態")
    left, right = st.columns(2)
    left.metric("Demo 時間", status["local_time"])
    right.metric("血壓", status["blood_pressure"] or "—")
    heart_rate = status["heart_rate_bpm"] or "—"
    sleep = f"{status['sleep_hours']:g} 小時" if status["sleep_hours"] is not None else "—"
    st.markdown(
        f"血壓等級：**{level_badge(status['alert_level'])}**　心率：{heart_rate}　睡眠：{sleep}"
    )
    st.markdown("\n".join(f"- {row}" for row in dose_rows(status["doses"])))

    st.subheader("🚨 警報")
    alerts = guarded(api.alerts) or []
    if not alerts:
        st.caption("目前沒有警報。")
    for alert in map(alert_row, alerts):
        (st.error if alert["urgent"] else st.warning)(alert["text"])

    st.subheader("🔧 後台事件")
    rows = activity_rows(guarded(api.activity, 12) or [])
    st.markdown("\n".join(f"- {row}" for row in rows) if rows else "（還沒有事件）")


with st.sidebar:
    st.header("Demo 順序")
    st.markdown(
        "1. **場景 A** → Agent 主動問候 → 說「吃了」\n"
        "2. **場景 B** → 說「我今天頭有點暈」\n"
        "3. **場景 C** → 說「我胸口有點悶」\n"
        "4. 再說一次胸悶 → 不會重複通報\n"
        "5. 問「我今天吃藥了嗎？」"
    )
    st.caption(f"API：{os.environ.get('API_URL', 'http://localhost:8001')}")

st.title("🏠 HomeWellness Companion")
st.caption("主動式健康關懷與用藥提醒｜預設離線：不連外網、不需金鑰")
brain = guarded(client.brain)
if brain:
    st.caption(f"大腦：{brain_label(brain)}")
if external_warning(brain):
    st.warning(external_warning(brain))

chat, devices, live = st.columns([5, 3, 4], gap="large")

# NOTE: Actions run before the views are drawn, so one click shows its result at once.
with devices:
    st.subheader("📡 裝置模擬器")
    st.caption("模擬手環經 MQTT 送資料。請依序 A → B → C。")
    for name, letter, title, hint in SCENARIOS:
        if st.button(f"▶ 場景 {letter}｜{title}", key=f"sc-{name}", help=hint):
            guarded(client.start_scenario, name)
        st.caption(hint)
    st.divider()
    if st.button("🔄 重置 Demo", key="reset", help="清除資料並把時間移回現在"):
        if guarded(client.reset) is not None:
            st.success("已重置，可以從場景 A 重來。")

with chat:
    st.subheader("💬 王奶奶 × 居家健康伴侶")
    history = st.container()
    st.caption("快捷回覆（Demo 用固定說法，確保 Agent 聽得懂）")
    chosen = None
    for row in (0, 2):
        for column, index in zip(st.columns(2), (row, row + 1), strict=True):
            if column.button(QUICK_REPLIES[index], key=f"q-{index}"):
                chosen = QUICK_REPLIES[index]
    message = chosen or st.chat_input("或自己輸入…")
    if message:
        with st.spinner("Agent 思考中…"):
            guarded(client.send_message, message)
    with history:
        conversation_view(client)

with live:
    status_view(client)
