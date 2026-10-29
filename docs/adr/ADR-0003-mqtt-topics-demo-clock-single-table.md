# ADR-0003: MQTT Topics, Demo Clock, Single-Table DynamoDB

Date: 2026-10-28
Status: Accepted

## Context
The worker must react to device data in real time. The live demo must show a morning scene at any hour of the day.
Alerts and intake records must be safe when requests repeat or race. DynamoDB access must stay simple.

## Decision
- Topics: `homewellness/<elder_id>/vitals`, `.../sleep`, and `homewellness/sim/clock`. Mosquitto stands in for AWS IoT Core (same protocol).
- The clock topic moves the worker clock. It works only when `DEMO_MODE=true`. Each scenario starts with one clock message.
- One DynamoDB table with keys PK and SK. Payloads are JSON text in `data`.
- Atomic conditional writes give idempotency (`CLAIM#`) and no double intake (`INTAKE#`). Reads are consistent.
- DynamoDB Local in Docker. `moto` served as the DynamoDB stand-in in the build sandbox.

## Alternatives Considered
- **LocalStack.** Community edition needs an auth token since release 2026.03.0 (checked October 2026). This breaks "no key". Rejected.
- **Real AWS.** Needs an account, network and a bill. Rejected.
- **In-memory fakes only.** No event story to show. Kept for unit tests.
- **Several tables.** More setup, no benefit at this size.
- **Native DynamoDB attributes.** The SDK rejects floats. JSON text avoids it and reads well in a demo.
- **Set the clock by an API call.** Couples the simulator to the API. A message keeps one path for all input.

## [Trade-off Analysis]
- Pros: the same path serves a real device and the simulator. One table is easy to explain. Conditional writes need no lock service.
- Cons: JSON text hides fields from DynamoDB queries. The clock message is a demo-only back door.
- Reason: a small PoC needs a clear story more than rich queries. The back door is off by default.

## Consequences
- Duplicates are removed by claims. A claim never expires, so a replay needs a reset (`make demo-reset`).
- Both stores (memory and DynamoDB) must pass the same contract tests.

## Verification
14 contract tests run on both stores. Ten parallel callers produced one claim, one intake, one alert and one trigger.
23 integration tests passed. A real worker process played the scenarios over a real broker.

Related: MEM-0003-phase-2-data-pipeline.md
