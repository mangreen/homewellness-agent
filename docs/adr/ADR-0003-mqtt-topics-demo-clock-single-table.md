# ADR-0003: MQTT Topics, Demo Clock, Single-Table DynamoDB

Date: 2026-10-28
Status: Accepted (short form. Expand after the demo.)

## Context
The worker must react to device data in real time. The live demo must show a morning scene at any
hour. DynamoDB access must stay simple and fast.

## Decision
- Topics: `homewellness/<elder_id>/vitals`, `.../sleep`, and `homewellness/sim/clock`.
- The clock topic moves the worker clock. It works only when `DEMO_MODE=true`.
- One DynamoDB table with keys PK and SK. Payloads are JSON text in `data`.
- Atomic conditional writes give idempotency (`CLAIM#`) and no double intake (`INTAKE#`).

## [Trade-off Analysis]
- Pros: the same MQTT path serves the real device and the simulator. One table is easy to explain.
  Conditional writes need no lock service.
- Cons: JSON text hides fields from DynamoDB queries. A clock message is a demo-only back door.
- Reason: a small PoC needs a clear story more than rich queries. The back door is off by default.

Related: MEM-0003-phase-2-data-pipeline.md, MEM-0002-mvc-architecture.md
