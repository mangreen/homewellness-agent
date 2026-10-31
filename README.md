# HomeWellness Companion (PoC)

A voice-style health companion for older adults. It reads device data and starts the conversation.
It reminds the person to take medicine. It alerts family when a rule says the situation is urgent.

This repository is a live-demo PoC. It runs offline. It needs no API key.

## Status

| Phase | Content | State |
| --- | --- | --- |
| 1, 1b | Foundation, models, controllers (MVC) | Done |
| 2 | DynamoDB stores, MQTT, device simulator | Done |
| 3 | Agent (LangChain, tools), HTTP API, terminal demo | Done |
| 4 | Streamlit demo UI, rehearsal, speaker script | Done |
| 5 | Complete decision records, error records, slides | Done |
| 6 | Real LLM providers (Claude, OpenAI, OpenRouter) with an offline fallback | Done, waiting for review |

## Requirements

- macOS with Docker Desktop. Tested target: Docker Engine 20.10, Compose v2.10.
- `git`, `curl`. No Python is needed on the host.

## Quick start

```bash
make test            # unit tests and the coverage gate (80%)
make itest           # integration tests: DynamoDB Local and Mosquitto
make demo-cli        # the whole story in the terminal (no other container, no network)
make up              # start everything. Demo page: http://localhost:8501. API: http://localhost:8001
make open            # open demo page: http://localhost:8501
make uitest          # tests of the page (stub API)
make rehearse        # the whole story through the real page and the real stack
make sim S=morning   # device scenario: morning, dizzy, crisis
make say T="我今天頭有點暈"
make alerts
make logs            # JSON logs with trace-id
make demo-reset      # clear data, then replay the scenarios
make down
```

The first build needs network access. After that, everything runs offline.
If your `.env` is older than `.env.example`, copy the new lines into it.

## Use a real LLM (optional)

The default brain is an offline scripted model. To use a real LLM you need a key and a network.

1. Edit `.env`: set `LLM_PROVIDER` to `anthropic`, `openai` or `openrouter`, and set the key of that provider.
   Optional: `LLM_MODEL` (default: `claude-haiku-5-5`, `gpt-5.4-mini`, `nvidia/nemotron-3-ultra-550b-a55b:free`).
2. `docker compose up -d app`, then `make brain` (or look under the page title) to see which brain answers.
3. `make llm-probe` checks the key, the network, the model and tool calling with two small calls. It shows the real cause of a failure.
4. `make llm-eval` runs nine fixed safety cases against that brain and shows the time of each. Run it before you demo with it.
   For a free model add `ARGS="--delay 5"` (rate limit). A large free model can need `LLM_TIMEOUT_SECONDS=60`.

If the provider fails, the offline model answers (`LLM_FALLBACK=true`). The timeline of the page shows why.
A long timeout means a long wait before that fallback. Check the speed in the report. Conversation data and health values
go to the provider. The demo elder is fictional. Do not type real personal data.
A free OpenRouter model can log prompts, and it may be slow or unavailable. Use the offline model for the formal demo.

## The demo story

Speaker script with timing and fallbacks: `docs/demo-script.md`.

1. **A:** the device sends sleep 4.5 h. The agent greets first and reminds the medicine.
2. **B:** the elder says she is dizzy. The agent reads the vitals by tool, asks the safety policy, and informs the family.
3. **C:** a critical reading arrives. The agent asks. The elder reports chest tightness. The policy calls for emergency help.
4. **D:** a repeat sends no second alert. The agent remembers the medicine.

## API

Interactive docs: http://localhost:8001/docs. Contract file: `docs/api/openapi.yaml`.
State-changing calls need an `Idempotency-Key` header. A duplicate gets `409`.
Errors have one shape and carry a `trace_id`.

## Architecture

MVC. See `docs/architecture/mvc-overview.md`. Models hold data and rules. Controllers take an input and
run the flow. Views format the output. Stores and services sit behind small interfaces.
The PoC uses these stand-ins:

| PoC | Real product |
| --- | --- |
| Mosquitto | AWS IoT Core |
| DynamoDB Local | Amazon DynamoDB |
| Scripted model (a real LangChain chat model) | A real LLM, for example Amazon Bedrock |
| Alert list | Amazon SNS |
| One uvicorn process | ECS Fargate, with shared state services |

## Trade-offs

The decision index is `docs/adr/README.md`. It lists every ADR, memory record and error record.

## Safety note

The agent does not diagnose and does not change medicine doses. The code policy decides on alerts, not the
model. Alert thresholds are demo values. A clinician must review them before any real use.
