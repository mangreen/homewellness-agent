# todo.md (Active Sprint Backlog)

## Phase 1: Foundation and core
- [x] Repository skeleton, Docker, Compose, Makefile, CI, pre-commit
- [x] Mermaid domain model, MEM-0001, ADR-0001
- [ ] Domain: vitals, alert policy, escalation rules
- [ ] Domain: medication, trigger policy
- [ ] Application: 4 use cases with in-memory adapters
- [ ] Coverage gate 80% on Domain and Application
- [ ] User runs `make up` and `make test` on the Mac

## Later
- Phase 2: DynamoDB adapter, MQTT worker, device simulator, claim store contract tests
- Phase 3: scripted chat model, agent tools, FastAPI, trace-id, JSON logs
- Phase 4: Streamlit UI, demo script, offline rehearsal
- After demo: complete MEM and ADR, write slides
