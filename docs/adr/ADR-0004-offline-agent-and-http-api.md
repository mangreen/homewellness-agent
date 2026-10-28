# ADR-0004: Offline Agent through LangChain, Tools Behind a Policy, Idempotent HTTP

Date: 2026-10-28
Status: Accepted (short form. Expand after the demo.)

## Context
The demo must run offline with no key. The assignment asks for LangChain, memory and tool calling.
Alerts must be safe: a wrong or repeated alert is a real problem.

## Decision
- The brain is `ScriptedChatModel`, a real LangChain chat model with keyword rules. It runs through
  `create_agent`, so the tool-calling loop is real. A real LLM replaces it in `bootstrap.py` only.
- Tools are bound to one elder per request. The model cannot choose another elder.
- `escalate_emergency` only asks. The code policy decides. A repeat in 10 minutes sends no second alert.
- Live blood pressure is read by tool, not put in the prompt.
- State-changing POST calls need an `Idempotency-Key`. A duplicate gets 409. A failed call frees the key.
- One process runs the API and the MQTT subscriber, because the demo clock and alert list live in it.

## [Trade-off Analysis]
- Pros: offline, free, repeatable demo. Same structure as a real agent. Safe by construction.
- Cons: the scripted brain does not understand free speech. One process does not scale out.
- Reason: the goal is to show the architecture and the idea. Scale-out is a later step
  (move the clock, alert list and subscriber to shared services).

## Consequences
- Prompt and model share a small text contract (`稱呼：`, `家屬：`, `現在時間：`, `[SYSTEM_EVENT]`).
  A test runs both together.
- A real LLM needs a new adapter, an API key from the environment, and a re-run of the behavior tests.

Related: MEM-0004-phase-3-agent-and-api.md, ADR-0002-lightweight-mvc.md
