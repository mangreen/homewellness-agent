# CLAUDE.md

Project: HomeWellness Companion PoC (proactive health care and medication reminder agent).
Goal: a live demo that runs offline. Show the architecture and the idea.

## Rules for the AI agent
- Follow the development rules (Staff Engineer System Prompt v3.0).
- Use TDD: write a failing test first. Then write the minimum code. Then refactor.
- Test names: `should_<behavior>_when_<condition>`. Use the AAA pattern.
- Use MVC (`docs/architecture/mvc-overview.md`). Keep `models/`, `views/` and `controllers/` free of SDK imports (boto3, paho).
  Import rules are tested in `tests/unit/test_architecture_rules.py`.
- Never hard-code a secret. Use environment variables. Update `.env.example`.
- Update `docs/architecture/mvc-overview.md` before you change a model.
- Write docs and comments in English (ASD-STE100). Demo text may use Traditional Chinese.
- Stop at the end of each phase. Ask the user to confirm.

## Commands (run on the host; Python runs in Docker)
- `make up` / `make down`: start or stop the stack.
- `make test`: run tests with the coverage gate (80%).
- `make lint`: run ruff. `make itest`: integration tests. `make demo-cli`: the demo story in the terminal.
- `make uitest`: tests of the Streamlit page. `make rehearse`: the whole story on the running stack.
- `make brain`: which brain answers. `make llm-eval`: behavior cases for the chosen brain (needs a key for a real one).
- `make openapi`: rewrite `docs/api/openapi.yaml` after an API change.

## Context
- Memory: `.agents/memories/`. Decisions: `docs/adr/` (index: `docs/adr/README.md`). Errors: `.agents/errors/`. Backlog: `todo.md`.
- Git: Phase Flow. Branch `phase/<n>-<name>`. Tag `phase-<n>-<name>` after merge.
