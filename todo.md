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

## Phase 2: Data and event pipeline
- [x] DynamoDB single-table stores with contract tests (memory and DynamoDB)
- [x] Concurrency: 10 parallel callers give one alert, one intake, one claim, one trigger
- [x] MQTT controller, subscriber, publisher, topics, bad-message handling
- [x] Demo clock, three scenarios, simulator CLI, worker, health endpoint
- [ ] User runs `make test`, `make itest`, `make up`, `make sim S=morning` on the Mac

## Phase 3: Agent and API
- [x] Scripted LangChain model, 4 tools bound to one elder, policy gate, proactive greeting
- [x] FastAPI: strict DTOs, Idempotency-Key (409), trace-id, sanitized errors, OpenAPI file
- [x] Demo story A to D as an API test and as `make demo-cli`
- [ ] User runs `make test`, `make itest`, `make up`, `make demo-cli`, `make say` on the Mac

## Later
- Phase 4: Streamlit UI, demo script, offline rehearsal
- After demo: complete MEM and ADR, write slides
