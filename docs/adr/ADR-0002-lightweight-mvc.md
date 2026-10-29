# ADR-0002: Lightweight MVC

Date: 2026-10-28
Status: Accepted
Supersedes: ADR-0001-hexagonal-with-swappable-adapters.md

## Context
ADR-0001 gave strong separation but too much structure for a demo: three layers, a port file, one class per use case.
Phase 3 adds an API and Phase 4 adds a UI. Both map directly to controllers and views. Reviewers know MVC well.

## Decision
Use MVC with a few support packages (`docs/architecture/mvc-overview.md`).
- Models: data classes and pure rules. Controllers: take an input and run the flow. Views: format output.
- Stores and services sit behind small Protocols in `interfaces.py`, so a real LLM, DynamoDB or SNS replaces a stand-in without a controller change.
- `bootstrap.py` is the only wiring module.
- A test reads the imports and enforces the rules (models and views have no SDK, controllers have no concrete store).

## Alternatives Considered
- **Keep Hexagonal.** Strongest separation. More files than the demo needs. Rejected by the user.
- **Active-record models** (data access inside the model). Fewer files. Rules would depend on I/O, and the offline tests would slow down. Rejected.
- **Flat scripts.** Fastest. No seams for a real LLM. Rejected.

## [Trade-off Analysis]
- Pros: easy to read, fewer files and concepts, a direct fit for the API and the UI.
- Cons: weaker layer discipline. The import test must replace it.
- Reason: this is a demo. The swap seams were the useful part of Hexagonal, and they stay.

## Consequences
- Names changed: `Repository` to `Store`, use case to controller method.
- The 122 tests of Phase 1 kept their behavior. The suite grew with each phase (357 unit tests at Phase 4).
- The swap is still proven by design and contract tests only.

## Verification
All 122 tests passed after the move. Six import-rule tests were added. The module map is in `mvc-overview.md`.

Related: ADR-0001-hexagonal-with-swappable-adapters.md, MEM-0002-mvc-architecture.md, MEM-0001-poc-scope-and-stack.md
