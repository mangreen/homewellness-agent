# HomeWellness Companion (PoC)

A voice-style health companion for older adults. It reads device data and starts
the conversation. It reminds the person to take medicine. It alerts family when
a rule says the situation is urgent.

This repository is a live-demo PoC. It runs offline. It needs no API key.

## Status

| Phase | Content | State |
| --- | --- | --- |
| 1 | Foundation, Domain, Application (in-memory) | Done, waiting for review |
| 2 | DynamoDB, MQTT, device simulator | Not started |
| 3 | Agent, API | Not started |
| 4 | Demo UI | Not started |

## Requirements

- macOS with Docker Desktop. Tested target: Docker Engine 20.10, Compose v2.10.
- `git`. No Python is needed on the host.

## Quick start

```bash
make test   # run unit tests and the coverage gate
make up     # start Mosquitto, DynamoDB Local, and the app placeholder
make down
```

The first build needs network access. After that, the stack runs offline.

## Architecture

See `docs/architecture/domain-model.md`. Layers: Domain, Application, Infrastructure.
Each external system sits behind a port. The PoC uses these stand-ins:

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
