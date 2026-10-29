# Changelog

## Unreleased
- Phase 4: Streamlit demo page, activity timeline, `POST /demo/reset`, `make uitest`, `make rehearse`, demo script.
- Phase 3: scripted LangChain agent with 4 tools, proactive greeting, FastAPI with idempotency and trace-id, OpenAPI file, `make demo-cli`, `make say`. The old worker and health modules are removed.
- Phase 2: DynamoDB stores, MQTT worker and publisher, demo clock, scenarios, simulator CLI, `make itest`, `make sim`.
- Phase 1b: refactor from DDD layers to lightweight MVC (models, stores, services, controllers, views). No behavior change.
- Phase 1: repository skeleton, Docker Compose (Mosquitto, DynamoDB Local, app placeholder).
- Phase 1: Domain rules (alert levels, escalation, medication intake, proactive triggers).
- Phase 1: Application use cases and in-memory adapters. 122 unit tests, 100% coverage.
