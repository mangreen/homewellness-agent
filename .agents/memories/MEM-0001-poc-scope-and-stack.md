# MEM: PoC Scope and Stack
Date: 2026-10-27
Status: Approved
Tags: scope, stack, offline, architecture

## Summary
The PoC runs offline, needs no API key, and shows the architecture and the idea.
(Short memo. Expand after the demo.)

## Details
### Context & Evolution
The project is a take-home demo for a Technical PM role. The demo is live.
The user set these limits: no paid service, no API key, no network at run time.

### Specification
- LLM brain: `ScriptedChatModel` (fake). It sits behind the `AgentRunner` port.
- Device channel: Mosquitto. It stands in for AWS IoT Core. Same MQTT protocol.
- Storage: DynamoDB Local. It stands in for Amazon DynamoDB.
- Notifications: a `Notifier` port. The PoC shows alerts in a UI panel.
- Layers: Domain, Application, Infrastructure, API. Package name: `homewellness`.
- All Python runs in Docker (host: macOS Big Sur, Docker Desktop 4.12).
- Git: Phase Flow. Tags: `phase-N-*`.
- Docs and code comments: English (ASD-STE100). Demo text: Traditional Chinese.
- Documentation debt: write short MEM and ADR now. Complete them after the demo.
- Not in scope: Bedrock, Claude API, voice, Langflow, daily reports.

## When to Use
Read this file when you decide scope, stack, or environment limits.
AI must IGNORE this spec if Status is Superseded.

Related: docs/adr/ADR-0001-hexagonal-with-swappable-adapters.md
