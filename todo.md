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

## Phase 4: Demo UI and rehearsal
- [x] Activity timeline and demo reset (API), device events, DynamoDB table reset
- [x] Streamlit page (chat, scenarios, status, alerts, timeline), quick replies, own image
- [x] UI tests (stub API) and `make rehearse` (whole story, real stack)
- [x] Demo script, offline rehearsal twice (no network namespace)
- [ ] User runs `make uitest`, `make rehearse`, `make up`, then the demo by hand with Wi-Fi off
- [ ] User records a backup screen video

## Phase 5: Decision records and slides
- [x] Slides (7 slides, 15 minutes) as a Slides artifact. Export to PDF or PowerPoint for the hand-in
- [x] MEM-0001 to 0005 and ADR-0001 to 0005 in full form, `docs/adr/README.md` index, three ERR records
- [x] Test for two-way links, headings and unfinished markers
- [ ] User checks the slides in the browser and exports PDF or PPTX
- [ ] User records the backup screen video

## Phase 6: Real LLM providers
- [x] Factory for Claude, OpenAI and OpenRouter, keys from the environment, hidden from logs
- [x] Offline fallback runner, `GET /demo/brain`, page label and data warning
- [x] Prompt rules for real models, behavior evaluation (`make llm-eval`)
- [x] Fake OpenAI-compatible server test, real Anthropic endpoint test with an invalid key
- [x] User ran `make llm-eval` with OpenRouter (free Nemotron, timeout 60 s): no FAIL
- [ ] User runs `make llm-probe` and `make llm-eval` for Claude and OpenAI if they want them
- [ ] User decides which brain to use in the formal demo (offline is the safe choice)

## Later
