# ADR-0005: Streamlit Demo UI over the HTTP API

Date: 2026-10-28
Status: Accepted (short form. Expand after the demo.)

## Context
The live demo needs one page that shows the dialogue, the device events and what happens behind the scenes.
The assignment names Streamlit. The laptop is old, so the API image must stay light.

## Decision
- The page is a Streamlit app in its own image (`ui/`). It uses the HTTP API only.
- Views refresh every 2 seconds with `st.fragment(run_every=...)`. A click runs its action before the views are drawn.
- Quick-reply buttons send fixed phrases. A test checks that the scripted agent understands each one.
- The API adds `GET /demo/activity` and `POST /demo/reset` (demo mode only) for the timeline and a one-click reset.
- `make rehearse` plays the whole story through the real page code (Streamlit `AppTest`) against the running stack.

## [Trade-off Analysis]
- Pros: matches the assignment, one clear screen, the same API as any other client, a testable rehearsal.
- Cons: polling instead of push, a second image (about 1 minute to build), fixed phrases limit free talk.
- Reason: polling every 2 seconds is simple and enough for a demo. Push (SSE) adds code with no demo value.

Related: MEM-0005-phase-4-demo-ui.md, ADR-0004-offline-agent-and-http-api.md
