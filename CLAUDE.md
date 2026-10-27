# CLAUDE.md

Project: HomeWellness Companion PoC (proactive health care and medication reminder agent).
Goal: a live demo that runs offline. Show the architecture and the idea.

## Rules for the AI agent
- Follow the development rules (Staff Engineer System Prompt v3.0).
- Use TDD: write a failing test first. Then write the minimum code. Then refactor.
- Test names: `should_<behavior>_when_<condition>`. Use the AAA pattern.
- Keep Domain and Application free of framework and SDK imports.
- Never hard-code a secret. Use environment variables. Update `.env.example`.
- Update `docs/architecture/domain-model.md` before you change the Domain layer.
- Write docs and comments in English (ASD-STE100). Demo text may use Traditional Chinese.
- Stop at the end of each phase. Ask the user to confirm.

## Commands (run on the host; Python runs in Docker)
- `make up` / `make down`: start or stop the stack.
- `make test`: run tests with the coverage gate (80%).
- `make lint`: run ruff.

## Context
- Memory: `.agents/memories/`. Decisions: `docs/adr/`. Backlog: `todo.md`.
- Git: Phase Flow. Branch `phase/<n>-<name>`. Tag `phase-<n>-<name>` after merge.
