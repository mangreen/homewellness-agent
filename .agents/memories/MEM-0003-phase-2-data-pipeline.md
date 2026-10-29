# MEM: Phase 2 Data Pipeline
Date: 2026-10-28
Status: Approved
Tags: mqtt, dynamodb, demo-clock, idempotency, scenarios

## Summary
A device message goes through MQTT and a controller into DynamoDB. A demo clock and three scenarios drive the story.

## Details
### Context & Evolution
Built on the MVC layout of MEM-0002-mvc-architecture.md. The decisions are in ADR-0003-mqtt-topics-demo-clock-single-table.md.
Phase 2 first had its own `worker.py` and `health.py`. Phase 3 replaced them with the FastAPI app (MEM-0004-phase-3-agent-and-api.md).

### Specification
**MQTT topics** (`topics.py`): `homewellness/<elder_id>/vitals`, `homewellness/<elder_id>/sleep`, `homewellness/sim/clock` (demo only).

**Payloads** (pydantic, unknown fields rejected)
- vitals: `measured_at` (with time zone), `systolic` and `diastolic` (both or none), `heart_rate_bpm`, `room_temperature_c`.
- sleep: `woke_on` (date), `hours_asleep`. clock: `now` (with time zone).
- A bad message is dropped and logged with the reason. The log never holds the payload.

**DynamoDB single table** (keys PK and SK, JSON text in `data`)

| PK | SK | Content |
| --- | --- | --- |
| `ELDER#<id>` | `VITALS#<utc time>` | one reading |
| `ELDER#<id>` | `SLEEP#<woke_on date>` | summary of the last night |
| `ELDER#<id>` | `INTAKE#<date>#<dose_id>` | one dose taken (conditional write) |
| `ELDER#<id>` | `TURN#<utc time>#<random>` | one conversation turn |
| `CLAIM#<key>` | `CLAIM` | idempotency or de-duplication key |

**Keys and windows**
- Trigger key: `trigger:<elder>:<dedup_key>`. The dedup key is `med:<date>:<dose>`, `vitals:<measured_at>` or `sleep:<date>`.
- Alert key: `escalation:<elder>:<key>`. A failed send frees the key.
- Reads use `ConsistentRead`. A vitals reading older than 30 minutes is not used.

**Scenarios** (`simulator/scenarios.py`; each starts with a clock message)
- morning: clock 08:05, sleep 4.5 h, vitals 128/82. dizzy: clock 08:20, vitals 158/98. crisis: clock 08:40, vitals 188/121.
- The worker removes duplicate triggers. Replay needs a reset.

**Operations**: `make sim S=<name>`, `make demo-reset`, `make itest`.

### Known Limits
- The elder profile is in memory (`demo.py`). Claims never expire.
- Integration tests ran on `moto` in the sandbox and on DynamoDB Local on the Mac.

## When to Use
Read this record when you change topics, payloads, the table layout or the stores.
AI must IGNORE this spec if Status is Superseded.

Related: ADR-0003-mqtt-topics-demo-clock-single-table.md, MEM-0002-mvc-architecture.md, MEM-0004-phase-3-agent-and-api.md
