# MEM: MVC Architecture
Date: 2026-10-28
Status: Approved
Tags: architecture, mvc, refactor, import-rules

## Summary
Updates/Supersedes the layer decision in MEM-0001-poc-scope-and-stack.md: the code uses lightweight MVC.
Behavior did not change. The 122 tests of Phase 1 passed before and after the move.

## Details
### Context & Evolution
Phase 1 used Domain, Application and Infrastructure layers with eight ports and one class per use case.
The user asked for a lighter design. The move was a refactor: files moved with `git mv`, names changed, tests stayed.
The map of old and new modules is in `docs/architecture/mvc-overview.md`. The reasons are in ADR-0002-lightweight-mvc.md.

### Specification
**Packages (under `src/homewellness/`)**

| Package | Role | May import |
| --- | --- | --- |
| `models/` | data classes and pure rules, no I/O | standard library |
| `stores/` | data access (in-memory, DynamoDB) | `models` |
| `services/` | clock, notifier, MQTT, agent runner, scripted model, activity log | `models`, `interfaces` |
| `controllers/` | take an input, run the flow | `models`, `views`, `interfaces` |
| `views/` | text for people and for the agent | `models` |
| `api/` | HTTP controllers and JSON shapes | `controllers`, `views`, `models`, `interfaces` |
| `interfaces.py` | small Protocols for what we may swap | `models` |

- `bootstrap.py` is the only module that knows the concrete stores, clock, notifier and LLM.
- `ui/` (outside `src/`) uses the HTTP API only. See `docs/architecture/mvc-overview.md`.

**Names**
- `*Repository` became `*Store`. A use case became a controller method: `ingest`, `record_intake`, `escalate`, `reply`.

**Rules**
- Models and views do not import SDKs. Controllers do not import `boto3`, `paho` or a concrete store.
- `tests/unit/test_architecture_rules.py` reads the imports with `ast` and fails on a violation.

### Known Limits
- The import test checks module names only. It does not check calls through objects.

## When to Use
Read this record when you add or move code. AI must IGNORE this spec if Status is Superseded.

Related: MEM-0001-poc-scope-and-stack.md, ADR-0002-lightweight-mvc.md, MEM-0003-phase-2-data-pipeline.md
