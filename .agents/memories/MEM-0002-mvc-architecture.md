# MEM: MVC Architecture
Date: 2026-10-28
Status: Approved
Tags: architecture, mvc, refactor

## Summary
Updates/Supersedes the layer decision in [MEM-0001](MEM-0001-poc-scope-and-stack.md): the code uses lightweight MVC.

## Details
### Context & Evolution
Phase 1 used Domain, Application, Infrastructure layers. The user asked for a lighter MVC design.
The change is a refactor. Behavior and tests stay the same. See ADR-0002.

### Specification
- Packages: `models`, `stores`, `services`, `controllers`, `views`, plus `interfaces.py` and `observability.py`.
- A controller imports models, views, and `interfaces` only. `bootstrap.py` builds concrete objects.
- Use cases became controller methods: `ingest`, `record_intake`, `escalate`, `reply`.
- `*Repository` became `*Store`.
- Map of old and new modules: `docs/architecture/mvc-overview.md`.
- Import rules are tested in `tests/unit/test_architecture_rules.py`.

## When to Use
Read this file when you add or move code. AI must IGNORE this spec if Status is Superseded.

Related: docs/adr/ADR-0002-lightweight-mvc.md
