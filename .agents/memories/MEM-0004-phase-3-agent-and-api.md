# MEM: Phase 3 Agent and API
Date: 2026-10-28
Status: Approved
Tags: agent, langchain, api, idempotency, tools

## Summary
Offline scripted agent on LangChain `create_agent`, four tools, FastAPI with idempotency and trace-id.

## Details
### Context & Evolution
Built on MEM-0002 (MVC) and MEM-0003 (pipeline). The old worker and health modules are replaced by
the FastAPI app (`homewellness.main:create_production_app`). See ADR-0004.

### Specification
- Run: `make up`. API on http://localhost:8001. Docs on `/docs`. Health on `/healthz`.
- Talk: `make say T="我今天頭有點暈"`. Alerts: `make alerts`. Scenarios: `make sim S=morning`.
- Terminal story (no Docker service): `make demo-cli` (add `ARGS=--step` to pause).
- Change the API, then run `make openapi`. A test fails if `docs/api/openapi.yaml` is old.
- Real LLM: add a branch in `bootstrap._build_model`. Keep `LANGSMITH_TRACING=false` offline.
- Run one uvicorn process only.

## When to Use
Read this file when you change the agent, the tools, the prompt, or the API.
AI must IGNORE this spec if Status is Superseded.

Related: docs/adr/ADR-0004-offline-agent-and-http-api.md
