# MEM: Phase 3 Agent and API
Date: 2026-10-28
Status: Approved
Tags: agent, langchain, tools, policy, api, idempotency

## Summary
An offline scripted agent runs on LangChain `create_agent` with four tools. FastAPI serves it with idempotency and trace-id.

## Details
### Context & Evolution
Built on MEM-0003-phase-2-data-pipeline.md. The decisions are in ADR-0004-offline-agent-and-http-api.md.
Phase 4 added the demo endpoints (MEM-0005-phase-4-demo-ui.md).

### Specification
**Tools** (each is bound to one elder; no tool takes an elder id)

| Tool | Result keys | Effect |
| --- | --- | --- |
| `get_latest_vitals` | `available`, `blood_pressure`, `level`, `heart_rate_bpm`, `measured_minutes_ago` | read |
| `get_medication_status` | `medication`, `doses[]` (`dose_id`, `label`, `time`, `state`) | read |
| `log_medication_intake` | `status` (recorded, already_taken, no_dose_due), `dose` | writes one intake |
| `escalate_emergency` | `status` (sent, suppressed_by_policy, duplicate), `action`, `reason` | the policy may refuse |

**Alert policy (demo values; a clinician must review them)**
- Levels: critical at 180/120 or more. High at 160/100. Elevated at 135/85. Low below 90 or below 60.
- Red flags: chest pain, shortness of breath, fainting.
- Red flag with low, high or critical pressure: call emergency (family and emergency services).
- Critical pressure, or a red flag at any level, or a symptom with abnormal pressure: notify family. Else: none.
- One alert per symptom set in a 10-minute window (agent key). The escalation controller adds its own key.

**Triggers**: medicine due (2 hours from the dose time), sleep under 5 hours, pressure low, high or critical.

**Prompt and event contract** (`views/agent_prompts.py`; the scripted model parses it)
- System prompt lines `稱呼：`, `家屬：`, `現在時間：`, then medicine, sleep, tone and safety rules. Live pressure is not in it.
- Event message: `[SYSTEM_EVENT] kind=... ; kind=...`. History is the last 10 turns.

**HTTP API** (`docs/api/openapi.yaml`; a test fails when the file is old; refresh with `make openapi`)
- State-changing POST needs `Idempotency-Key` (8 to 64 characters of `A-Za-z0-9._:-`). A duplicate gets 409. A failure frees the key.
- Error body: `{"error": {"code", "message", "trace_id"}}`. Codes: invalid_idempotency_key 400, elder_not_found 404, duplicate_request 409, validation_error 422, invalid_request 422, agent_unavailable 503, internal_error 500.
- Message text: 1 to 500 characters, unknown fields rejected. Elder id: `A-Za-z0-9_-`, up to 64 characters.
- Logs are JSON with `trace_id` and `user_id`. They hold the error type only. A new trace-id starts at each request and each MQTT message.

**Operations**: `make up` (API on :8001, docs on /docs), `make say T="..."`, `make alerts`, `make demo-cli`.

### Known Limits
- Run one uvicorn process: the clock, the alert list and the subscriber live in it.
- The scripted model knows fixed phrases only. There is no authentication.
- Real LLM providers: see MEM-0006-real-llm-providers.md (Phase 6).

## When to Use
Read this record when you change the agent, the tools, the prompt, the policy or the API.
AI must IGNORE this spec if Status is Superseded.

Related: ADR-0004-offline-agent-and-http-api.md, MEM-0003-phase-2-data-pipeline.md, MEM-0005-phase-4-demo-ui.md, MEM-0006-real-llm-providers.md
