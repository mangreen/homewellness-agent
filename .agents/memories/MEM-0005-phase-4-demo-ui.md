# MEM: Phase 4 Demo UI
Date: 2026-10-28
Status: Approved
Tags: ui, streamlit, demo, rehearsal, offline

## Summary
A Streamlit page, an activity timeline, a one-click reset, a rehearsal test and a speaker script.

## Details
### Context & Evolution
Built on MEM-0004-phase-3-agent-and-api.md. The decisions are in ADR-0005-streamlit-demo-ui.md.
The speaker script is `docs/demo-script.md` (Traditional Chinese). The slides are a separate deck.

### Specification
- Run: `make up`, then open http://localhost:8501 (`make open`). The UI container reads `API_URL`.
- Page: chat with four quick replies (left), three scenario buttons and reset (middle), status, alerts and timeline (right).
- Widget keys: `sc-morning`, `sc-dizzy`, `sc-crisis`, `reset`, `q-0` to `q-3`. Tests use these keys.
- Views refresh every 2 seconds. An action runs before the views are drawn.
- Demo endpoints (demo mode only): `GET /demo/activity` and `POST /demo/reset`. Reset drops and creates the DynamoDB table.
- Tests: `make uitest` (stub API), `make rehearse` (whole story on the real stack). A main-repo test checks every quick reply.
- Offline proof: the stack ran inside a Linux network namespace that had only loopback. The rehearsal passed twice.

### Known Limits
- Streamlit turns a leading emoji of an alert into its icon. Tests must match the text, not the emoji.
- Draw every widget in every run. Do not write `button or st.chat_input(...)`: the box would vanish after a click.
- The agent knows fixed phrases only. Use the buttons in the demo.
- A backup screen video is not in the repository. The user must record it.

## When to Use
Read this record when you change the page, the demo endpoints or the rehearsal.
AI must IGNORE this spec if Status is Superseded.

Related: ADR-0005-streamlit-demo-ui.md, MEM-0004-phase-3-agent-and-api.md
