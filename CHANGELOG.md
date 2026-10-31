# Changelog

## Unreleased
- Phase 6: `make llm-probe`, causes and times in the evaluation report, stricter prompt rules for real models, reason in the fallback event.
- Phase 6: real LLM providers (Claude, OpenAI, OpenRouter) behind `LLM_PROVIDER`, offline fallback, `GET /demo/brain`, `make llm-eval`, `make brain`.
- Phase 5: complete decision records (ADR and MEM), decision index, three error records, a test that keeps them linked.
- Phase 4: Streamlit demo page, activity timeline, `POST /demo/reset`, `make uitest`, `make rehearse`, demo script.
- Phase 3: scripted LangChain agent with 4 tools, proactive greeting, FastAPI with idempotency and trace-id, OpenAPI file, `make demo-cli`, `make say`. The old worker and health modules are removed.
- Phase 2: DynamoDB stores, MQTT worker and publisher, demo clock, scenarios, simulator CLI, `make itest`, `make sim`.
- Phase 1b: refactor from DDD layers to lightweight MVC (models, stores, services, controllers, views). No behavior change.
- Phase 1: repository skeleton, Docker Compose (Mosquitto, DynamoDB Local, app placeholder).
- Phase 1: Domain rules (alert levels, escalation, medication intake, proactive triggers).
- Phase 1: Application use cases and in-memory adapters. 122 unit tests, 100% coverage.
