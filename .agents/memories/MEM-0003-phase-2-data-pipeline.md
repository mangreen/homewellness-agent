# MEM: Phase 2 Data Pipeline
Date: 2026-10-28
Status: Approved
Tags: mqtt, dynamodb, demo, idempotency

## Summary
Device message to MQTT to controller to DynamoDB, with a demo clock and three scenarios.

## Details
### Context & Evolution
Built on the MVC layout from MEM-0002. See ADR-0003.
2026-10-28: Phase 3 replaced `worker.py` and `health.py` with the FastAPI app. See MEM-0004.

### Specification
- Run: the API app (MEM-0004). Healthy = connected to the broker and subscribed.
- Play a scenario: `make sim S=morning|dizzy|crisis`. Reset: `make demo-reset`.
- Order of scenarios: morning, dizzy, crisis. The worker removes duplicate triggers, so replay needs a reset.
- Tests: `make test` (unit), `make itest` (DynamoDB Local and Mosquitto).
- The elder profile is in memory (`demo.py`). Telemetry, intakes, claims, and turns use DynamoDB.
- Triggers are logged, kept in `container.triggers`, and handed to the agent (Phase 3).

## When to Use
Read this file when you change the worker, the topics, or the stores.
AI must IGNORE this spec if Status is Superseded.
