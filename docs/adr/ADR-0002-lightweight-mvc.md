# ADR-0002: Lightweight MVC

Date: 2026-10-28
Status: Accepted (short form. Expand after the demo.)
Supersedes: ADR-0001-hexagonal-with-swappable-adapters.md

## Context
ADR-0001 chose Hexagonal architecture. The PoC is small. The layers (Domain, Application,
Infrastructure), the port file, and one class per use case added more structure than the demo needs.
Phase 3 adds an API and Phase 4 adds a UI. Both map directly to controllers and views.

## Decision
Use MVC with a few support packages. See `docs/architecture/mvc-overview.md`.
- Models: data classes and pure business rules.
- Controllers: take an input and run the flow.
- Views: format output for people.
- Stores and services sit behind small Protocols in `interfaces.py`, so that a real
  LLM, DynamoDB, or SNS can replace a stand-in without a controller change.
- A small test checks the import rules.

## [Trade-off Analysis]
- Pros: easy to read, fewer files and concepts, a direct fit for the API and UI work.
- Cons: weaker layer discipline. The import-rule test must replace it.
- Reason: this is a demo PoC. The swap seams were the useful part of Hexagonal, and they stay.

## Consequences
- Use cases are now controller methods. Repositories are now stores.
- The swap is still proven by design and contract tests only. It is not proven on real AWS.

Related: MEM-0002-mvc-architecture.md
