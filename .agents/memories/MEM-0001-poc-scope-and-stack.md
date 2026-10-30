# MEM: PoC Scope and Stack
Date: 2026-10-27
Status: Approved (the layer decision is superseded by MEM-0002-mvc-architecture.md)
Tags: scope, stack, offline, environment, workflow

## Summary
The PoC runs offline, needs no API key, and shows the architecture and the idea in a live demo.
The layer decision of this record is superseded by MEM-0002-mvc-architecture.md.

## Details
### Context & Evolution
The project is a take-home demo for a Technical PM role (AI and IoT). The demo is live and lasts 15 minutes.
The user set four limits: no paid service, no API key, no network at run time, and a fast schedule.
2026-10-28: the user asked for a lighter architecture. See MEM-0002-mvc-architecture.md and ADR-0002-lightweight-mvc.md.
2026-10-29: the short records were completed. The scope did not change.

### Specification
**Environment (fixed by the user)**
- Host: MacBook Pro 2014, dual-core i7, 16 GB, no GPU. macOS Big Sur 11.7.
- Docker Desktop 4.12.0, Engine 20.10.17, Compose v2.10.2. Do not use newer Compose flags.
- All Python runs in Docker. The host needs Docker, git and curl only.

**Stack (pinned in `requirements*.txt` and `ui/requirements*.txt`)**
- Python 3.11 (image `python:3.11-slim-bookworm`). LangChain 1.4.7, LangGraph 1.2.18, FastAPI 0.162.0, uvicorn 0.54.0.
- pydantic 2.14.1, boto3 1.43.119, paho-mqtt 2.1.0. Streamlit 1.66.1 (own image).
- Mosquitto 2.0.18 and DynamoDB Local 2.5.2 (images can be overridden in `.env`).
- ~~Layers: Domain, Application, Infrastructure, API~~ DEPRECATED: superseded by MEM-0002-mvc-architecture.md (MVC).

**Stand-ins for the real product**
- LLM: `ScriptedChatModel`, a real LangChain chat model with keyword rules (default). Real providers since Phase 6: see MEM-0006-real-llm-providers.md.
- Device channel: Mosquitto for AWS IoT Core. Storage: DynamoDB Local for Amazon DynamoDB.
- Notifications: an alert list for Amazon SNS. The demo UI shows the list.

**Workflow**
- Git: Phase Flow. Branch `phase/<n>-<name>`. Tag `phase-<n>-<name>` after the merge.
- Phases: 1 foundation, 1b MVC refactor, 2 pipeline, 3 agent and API, 4 demo UI, 5 slides and records.
- Method: TDD (red, green, refactor). Coverage gate 80% (the code reaches 100%). Conventional Commits.
- Language: docs and code comments in English (ASD-STE100). Demo text, prompts and slides in Traditional Chinese.
- Secrets: none are needed. `.env` is ignored by git. Placeholders use `changeme`.

**Out of scope**
- Amazon Bedrock, voice (STT and TTS), Langflow, daily reports, authentication, multi-elder support. (A real LLM was out of scope until Phase 6.)

### Known Limits
- Docker could not run in the build sandbox. The user verifies each phase on the Mac.
- All alert thresholds are demo values. A clinician must review them.

## When to Use
Read this record when you decide scope, stack or environment limits.
AI must IGNORE the layer bullet of this spec. It is superseded.

Related: ADR-0001-hexagonal-with-swappable-adapters.md, ADR-0002-lightweight-mvc.md, MEM-0002-mvc-architecture.md, MEM-0006-real-llm-providers.md
