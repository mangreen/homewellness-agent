# ADR-0001: Hexagonal Architecture with Swappable Adapters

Date: 2026-10-27
Status: Superseded by ADR-0002-lightweight-mvc.md (2026-10-28)

DEPRECATED: read this record for history only. The swap seams of this design stay in ADR-0002-lightweight-mvc.md.

## Context
The demo must run offline. The real product uses AWS and a real LLM. The demo must show the path from one to the other.
Phase 1 had to produce safe, testable rules (alert levels, escalation, medicine intake, triggers) before any I/O existed.

## Decision
Use Ports and Adapters (Hexagonal). The Domain and Application layers import no framework and no SDK.
Each external system has one port and one in-memory adapter. Real adapters (DynamoDB, MQTT, LLM) come later without a Domain change.
Use cases are classes with one `execute` method.

## Alternatives Considered
- **Direct implementation** (SDK calls inside handlers). Fastest to write. Hard to test and hard to swap. Rejected.
- **Plain layers without ports.** Simpler. A change of database would touch the services. Rejected.
- **Microservices per capability.** Too heavy for a 2014 laptop and a PoC. Rejected.

## [Trade-off Analysis]
- Pros: fast unit tests, offline demo, a clear path to AWS, safety rules free of I/O.
- Cons: many files and interfaces for a small PoC. Eight ports, one class per use case.
- Reason: the rules had to be proven before I/O. The cost was acceptable in Phase 1. It grew in later phases.

## Consequences
- Phase 1 ended with 122 unit tests and 100% coverage on Domain and Application.
- The swap is proven by design and contract tests only. It is not proven on real AWS.
- The structure felt heavy for a demo. The user asked for a lighter one. This record is superseded for that reason.

## Verification
122 unit tests passed in Docker (Python 3.11). A mutation check (change `>=` to `>` and similar) made the tests fail each time.

Related: ADR-0002-lightweight-mvc.md, MEM-0001-poc-scope-and-stack.md
