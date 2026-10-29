# HomeWellness Companion (PoC)

A voice-style health companion for older adults. It reads device data and starts
the conversation. It reminds the person to take medicine. It alerts family when
a rule says the situation is urgent.

This repository is a live-demo PoC. It runs offline. It needs no API key.

## Status

| Phase | Content | State |
| --- | --- | --- |
| 1 | Foundation, models, controllers (in-memory) | Done |
| 1b | Refactor from DDD layers to MVC | Done |
| 2 | DynamoDB stores, MQTT worker, device simulator | Done, waiting for review |
| 3 | Agent, API | Not started |
| 4 | Demo UI | Not started |

## Requirements

- macOS with Docker Desktop. Tested target: Docker Engine 20.10, Compose v2.10.
- `git`. No Python is needed on the host.

## Quick start

```bash
make test        # unit tests and the coverage gate (80%)
make itest       # integration tests: DynamoDB Local and Mosquitto
make up          # start Mosquitto, DynamoDB Local and the worker
make sim S=morning   # play a scenario: morning, dizzy, crisis
make logs        # JSON logs with trace-id
make demo-reset  # clear data, then replay the scenarios
make down
```

If your `.env` is older than `.env.example`, copy the new lines into it.

The first build needs network access. After that, the stack runs offline.

## Architecture

MVC. See `docs/architecture/mvc-overview.md`. Models hold data and rules. Controllers take an input and
run the flow. Views format the output. Stores and services sit behind small interfaces.
The PoC uses these stand-ins:

| PoC | Real product |
| --- | --- |
| Mosquitto | AWS IoT Core |
| DynamoDB Local | Amazon DynamoDB |
| Scripted fake model | A real LLM (for example Amazon Bedrock) |
| Alert panel | Amazon SNS |

## Trade-offs

See `docs/adr/` and `.agents/memories/`.

## Safety note

The agent does not diagnose and does not change medicine doses. Alert thresholds
are demo values. A clinician must review them before any real use.
