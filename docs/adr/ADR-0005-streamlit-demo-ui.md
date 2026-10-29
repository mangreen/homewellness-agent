# ADR-0005: Streamlit Demo UI over the HTTP API

Date: 2026-10-28
Status: Accepted

## Context
The live demo needs one page that shows the dialogue, the device events and what happens behind the scenes.
The assignment names Streamlit. The laptop is old, so the API image must stay light.

## Decision
- The page is a Streamlit app in its own image (`ui/`). It uses the HTTP API only, through one client class.
- Views refresh every 2 seconds (`st.fragment(run_every=...)`). A click runs its action before the views are drawn.
- Quick-reply buttons send fixed phrases. A test checks that the scripted agent understands each one.
- The API adds `GET /demo/activity` and `POST /demo/reset` (demo mode only) for the timeline and a one-click reset.
- `make rehearse` plays the whole story through the real page code (Streamlit `AppTest`) on the running stack.

## Alternatives Considered
- **Plain HTML from FastAPI.** Lighter, but the assignment names Streamlit and the page would need its own JavaScript.
- **React.** A heavy toolchain for an old laptop. Rejected.
- **Terminal only.** Kept as the backup (`make demo-cli`).
- **Browser tests (Playwright).** Heavy to install on the old Mac. `AppTest` runs the same page code headless.
- **Push updates (SSE or WebSocket).** More code, no demo value at this size.
- **Reset by restarting containers only.** Works (`make demo-reset`), but needs the terminal during the demo.

## [Trade-off Analysis]
- Pros: matches the assignment, one clear screen, the same API as any other client, a testable rehearsal.
- Cons: polling instead of push, a second image (about one minute to build), fixed phrases limit free talk.
- Reason: polling every 2 seconds is simple and enough. Push adds code without demo value.

## Consequences
- The UI never imports backend code. The OpenAPI file is the contract.
- Streamlit turns a leading emoji of an alert into its icon, so tests match the text only.

## Verification
26 page tests passed with a stub API. The whole story passed twice through the real page on the full stack,
inside a Linux network namespace with no network (offline proof). The Streamlit server answered its health check.

Related: MEM-0005-phase-4-demo-ui.md
