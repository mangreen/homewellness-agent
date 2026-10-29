# ADR-0004: Offline Agent through LangChain, Tools Behind a Policy, Idempotent HTTP

Date: 2026-10-28
Status: Accepted

## Context
The demo must run offline with no key. The assignment asks for LangChain, memory and tool calling.
A wrong or repeated alert is a real harm, so alerts need a safe design.

## Decision
- The brain is `ScriptedChatModel`, a real LangChain chat model with keyword rules. It runs through `create_agent`, so the tool-calling loop is real.
- A real LLM replaces it in `bootstrap._build_model` only.
- Each tool is bound to one elder. The model cannot choose another elder.
- `escalate_emergency` only asks. The code policy decides. A repeat within 10 minutes sends no second alert.
- Live blood pressure is read by tool. It is not in the prompt. The prompt holds the slow facts: medicine, sleep, history.
- State-changing POST calls need an `Idempotency-Key`. A duplicate gets 409. A failure frees the key.
- One process runs the API and the MQTT subscriber, because the demo clock and the alert list live in it.

## Alternatives Considered
- **Local LLM (Ollama).** The CPU-only laptop is too slow, and a model download needs a network. Rejected.
- **Rule-only chatbot without LangChain.** Does not show the architecture the assignment asks for. Rejected.
- **Hosted LLM or Bedrock.** Needs a key and a network. Kept as the next step.
- **Langflow.** Heavy for the laptop and hard to test. Rejected.
- **Vitals in the prompt.** No tool-calling story and stale data risk. Rejected.
- **Replay the first response on a duplicate.** Needs response storage. A 409 is simpler and matches the spec.
- **Separate worker and API processes.** Needs shared state first. A later step.

## [Trade-off Analysis]
- Pros: offline, free, repeatable demo. The structure matches a real agent. Alerts are safe by design.
- Cons: the scripted brain does not understand free speech. One process does not scale out.
- Reason: the goal is to show architecture and idea. Scale-out needs the clock, alert list and subscriber in shared services.

## Consequences
- The prompt and the model share a small text contract (`稱呼：`, `家屬：`, `現在時間：`, `[SYSTEM_EVENT]`). Tests run both together.
- A real LLM needs an adapter, a key from the environment and new behavior tests (no diagnosis, no dose advice, one question).

## Verification
The whole story (scenes A to D) runs as an API test and in `make demo-cli`. Ten same-key requests gave one 200 and nine 409.
Ten chest-pain requests with different keys sent one alert. A real uvicorn process passed a smoke test.

Related: MEM-0004-phase-3-agent-and-api.md
