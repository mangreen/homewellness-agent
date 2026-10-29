# todo.md (Active Sprint Backlog)

## Phase 1: Foundation and core
- [x] Repository skeleton, Docker, Compose, Makefile, CI, pre-commit
- [x] Mermaid domain model, MEM-0001, ADR-0001
- [x] Domain: vitals, alert policy, escalation rules
- [x] Domain: medication, trigger policy
- [x] Application: 4 use cases with in-memory adapters
- [x] Coverage gate 80% on Domain and Application
- [ ] User runs `make test` and `make up` on the Mac and reports the result

## Phase 1b: MVC refactor
- [x] Mermaid overview, ADR-0002, MEM-0002
- [x] Move code to MVC packages, keep 122 tests green (now 128 with import rules)
- [x] Import-rule test

## Later
- Phase 2: DynamoDB adapter, MQTT worker, device simulator, claim store contract tests
- Phase 3: scripted chat model, agent tools, FastAPI, trace-id, JSON logs
- Phase 4: Streamlit UI, demo script, offline rehearsal
- After demo: complete MEM and ADR, write slides
