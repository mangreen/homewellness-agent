# MEM: Phase 4 Demo UI
Date: 2026-10-28
Status: Approved
Tags: ui, streamlit, demo, rehearsal

## Summary
Streamlit page, activity timeline, one-click reset, rehearsal test and a speaker script.

## Details
### Context & Evolution
Built on MEM-0004 (agent and API). See ADR-0005. The script is `docs/demo-script.md` (Traditional Chinese).

### Specification
- Run: `make up`, then open http://localhost:8501 (`make open`).
- Tests: `make uitest` (stub API, fast), `make rehearse` (the whole story on the real stack).
- Change the quick replies in `ui/view_models.py`. A main-repo test checks that the agent understands them.
- Streamlit turns a leading emoji of a message into the icon. Tests must not match on that emoji.
- The UI never imports backend code. It knows only the HTTP contract (`docs/api/openapi.yaml`).

## When to Use
Read this file when you change the page, the demo endpoints, or the rehearsal.
AI must IGNORE this spec if Status is Superseded.

Related: docs/adr/ADR-0005-streamlit-demo-ui.md
