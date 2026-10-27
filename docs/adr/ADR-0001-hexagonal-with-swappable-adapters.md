# ADR-0001: Hexagonal Architecture with Swappable Adapters

Date: 2026-10-27
Status: Accepted (short form. Expand after the demo.)

## Context
The demo must run offline. The real product uses AWS and a real LLM.
The demo must show how to move from one to the other.

## Decision
Use Ports and Adapters. The Domain and Application layers do not import any
framework or SDK. Each external system has one port and one in-memory adapter.
Real adapters (DynamoDB, MQTT, LLM) are added later without a Domain change.

## Consequences
- Pros: fast unit tests, offline demo, a clear path to AWS.
- Cons: more files and interfaces than a direct implementation.
- Risk: a swap is proven by design and contract tests only. It is not proven on real AWS.

Related: MEM-0001-poc-scope-and-stack.md
